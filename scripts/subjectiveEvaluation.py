import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
import math
from functools import reduce
from tqdm import tqdm
import warnings
import os
import matplotlib.pyplot as plt

def pairwise_result_matrices(df, normalize=False):
    """
    Creates three pairwise matrices:
    weak, strong, and tie
    with fixed model ordering.
    """

    ORDER = ["gt", "nn", "easing", "slerp", "noise"]

    # Keep only systems that exist in data (but preserve order)
    systems = [s for s in ORDER if s in set(df["left"]).union(set(df["right"]))]

    weak_matrix = pd.DataFrame(0, index=systems, columns=systems)
    strong_matrix = pd.DataFrame(0, index=systems, columns=systems)
    tie_matrix = pd.DataFrame(0, index=systems, columns=systems)

    for _, row in df.iterrows():
        left = row["left"]
        right = row["right"]
        choice = row["choice"]

        # skip unknown labels safely
        if left not in systems or right not in systems:
            continue

        if choice == -1:
            weak_matrix.loc[left, right] += 1

        elif choice == -2:
            strong_matrix.loc[left, right] += 1

        elif choice == 1:
            weak_matrix.loc[right, left] += 1

        elif choice == 2:
            strong_matrix.loc[right, left] += 1

        elif choice == 0:
            tie_matrix.loc[left, right] += 1
            tie_matrix.loc[right, left] += 1

    if normalize:
        weak_matrix = weak_matrix.div(weak_matrix.sum(axis=1), axis=0).fillna(0)
        strong_matrix = strong_matrix.div(strong_matrix.sum(axis=1), axis=0).fillna(0)
        tie_matrix = tie_matrix.div(tie_matrix.sum(axis=1), axis=0).fillna(0)

    return weak_matrix, strong_matrix, tie_matrix

def compute_mle_elo(df, SCALE = 400, BASE = 10, INIT_RATING = 1000):
    # Weak win
    ptbl_a_win_weak = pd.pivot_table(
        df[(df["choice"] == -1)],
        index="left",
        columns="right",
        values="choice",
        aggfunc="count",
        fill_value=0,
    )

    ptbl_a_win_strong = pd.pivot_table(
        df[(df["choice"] == -2)],
        index="left",
        columns="right",
        values="choice",
        aggfunc="count",
        fill_value=0,
    )

    ptbl_tie = pd.pivot_table(
        df[(df["choice"] == 0)],
        index="left",
        columns="right",
        values="choice",
        aggfunc="count",
        fill_value=0,
    )
    ptbl_tie = ptbl_tie + ptbl_tie.T

    ptbl_b_win_weak = pd.pivot_table(
        df[(df["choice"] == 1)],
        index="left",
        columns="right",
        values="choice",
        aggfunc="count",
        fill_value=0,
    )

    ptbl_b_win_strong = pd.pivot_table(
        df[(df["choice"] == 2)],
        index="left",
        columns="right",
        values="choice",
        aggfunc="count",
        fill_value=0,
    )

    ptbl_win = (
        ptbl_a_win_weak * 2
        + ptbl_b_win_weak.T * 2
        + ptbl_a_win_strong * 4
        + ptbl_b_win_strong.T * 4
        + ptbl_tie
    )

    models = pd.Series(np.arange(len(ptbl_win.index)), index=ptbl_win.index)
    p = len(models)
    X = np.zeros([p * (p - 1) * 2, p])
    Y = np.zeros(p * (p - 1) * 2)

    cur_row = 0
    sample_weights = []
    for m_a in ptbl_win.index:
        for m_b in ptbl_win.columns:
            if m_a == m_b:
                continue
            # if nan skip
            if math.isnan(ptbl_win.loc[m_a, m_b]) or math.isnan(ptbl_win.loc[m_b, m_a]):
                continue
            X[cur_row, models[m_a]] = +math.log(BASE)
            X[cur_row, models[m_b]] = -math.log(BASE)
            Y[cur_row] = 1.0
            sample_weights.append(ptbl_win.loc[m_a, m_b])

            X[cur_row + 1, models[m_a]] = math.log(BASE)
            X[cur_row + 1, models[m_b]] = -math.log(BASE)
            Y[cur_row + 1] = 0.0
            sample_weights.append(ptbl_win.loc[m_b, m_a])
            cur_row += 2
    X = X[:cur_row]
    Y = Y[:cur_row]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        lr = LogisticRegression(fit_intercept=False, penalty=None, tol=1e-6)
        lr.fit(X, Y, sample_weight=sample_weights)
    elo_scores = SCALE * lr.coef_[0] + INIT_RATING

    return pd.Series(elo_scores, index=models.index).sort_values(ascending=False)

def win_rate_split_ties(df):
    tie_df = df[df["choice"] == 0]
    weak_pref_df = df[df["choice"].isin([-1, 1])]
    strong_pref_df = df[df["choice"].isin([-2, 2])]

    win_counts = [
        weak_pref_df[weak_pref_df["choice"] == -1]["left"].value_counts(),
        weak_pref_df[weak_pref_df["choice"] == 1]["right"].value_counts(),
        2*strong_pref_df[strong_pref_df["choice"] == -2]["left"].value_counts(),
        2*strong_pref_df[strong_pref_df["choice"] == 2]["right"].value_counts(),
        tie_df["left"].value_counts()/2,
        tie_df["right"].value_counts()/2,
    ]

    appearance_counts = [
        weak_pref_df["left"].value_counts(),
        weak_pref_df["right"].value_counts(),
        2*strong_pref_df["left"].value_counts(),
        2*strong_pref_df["right"].value_counts(),
        tie_df["left"].value_counts(),
        tie_df["right"].value_counts(),
    ]

    total_wins = reduce(lambda a, b: a.add(b, fill_value=0), win_counts)
    total_appearances = reduce(lambda a, b: a.add(b, fill_value=0), appearance_counts)

    # Compute win rate
    win_rate = total_wins / total_appearances
    return win_rate.sort_values(ascending=False).rename(None)

def bootstrap_elo(df, bootstrap_rounds, bootstrap_users=True, seed=42):
    np.random.seed(seed)
    bootstrap_rows = []

    rows = []
    if bootstrap_users:
        # Pre-group all user data once
        user_groups_dict = dict(tuple(df.groupby("userID")))
        users = list(user_groups_dict.keys())

        for _ in tqdm(range(bootstrap_rounds), desc="bootstrap"):
            if bootstrap_users:
                # Sample user IDs (not DataFrame)
                sampled_users = np.random.choice(users, size=len(users), replace=True)

                # Collect all rows via list comprehension (avoid concat in loop)
                sampled_dfs = [user_groups_dict[u] for u in sampled_users]
                battle_sample = pd.concat(sampled_dfs, ignore_index=True)
            else:
                battle_sample = df.sample(frac=1.0, replace=True)

            # Append result of the scoring function
            rows.append(compute_mle_elo(battle_sample))

    # Return columns sorted by median value
    df = pd.DataFrame(rows)
    bootstrap_elo_lu = df[df.median().sort_values(ascending=False).index]
    os.makedirs("output", exist_ok=True)
    bootstrap_elo_lu.to_csv("output/bootstrap_elo_lu.csv")
    return bootstrap_elo_lu

def bootstrap_win_rate(df, bootstrap_rounds, bootstrap_users=True, seed=42):
    np.random.seed(seed)
    bootstrap_rows = []

    rows = []
    if bootstrap_users:
        # Pre-group all user data once
        user_groups_dict = dict(tuple(df.groupby("userID")))
        users = list(user_groups_dict.keys())

        for _ in tqdm(range(bootstrap_rounds), desc="bootstrap"):
            if bootstrap_users:
                # Sample user IDs (not DataFrame)
                sampled_users = np.random.choice(users, size=len(users), replace=True)

                # Collect all rows via list comprehension (avoid concat in loop)
                sampled_dfs = [user_groups_dict[u] for u in sampled_users]
                battle_sample = pd.concat(sampled_dfs, ignore_index=True)
            else:
                battle_sample = df.sample(frac=1.0, replace=True)

            # Append result of the scoring function
            rows.append(win_rate_split_ties(battle_sample))

    # Return columns sorted by median value
    df = pd.DataFrame(rows)
    bootstrap_wr_lu = df[df.median().sort_values(ascending=False).index]
    os.makedirs("output", exist_ok=True)
    bootstrap_wr_lu.to_csv("output/bootstrap_wr_lu.csv")
    return bootstrap_wr_lu

def win_rate_confidence_intervals(win_rate_df, alpha = 0.05):
    return pd.DataFrame({
        "wr_median": win_rate_df.median(),
        "wr_mean": win_rate_df.mean(),
        "wr_lower": win_rate_df.quantile(alpha/2),
        "wr_upper": win_rate_df.quantile(1-alpha/2),
        "wr_std": win_rate_df.std()
    })

def bootstrap_elo_confidence_intervals(bootstrap_elo_df, alpha = 0.05):
    return pd.DataFrame({
        "elo_median": bootstrap_elo_df.median(),
        "elo_mean": bootstrap_elo_df.mean(),
        "elo_lower": bootstrap_elo_df.quantile(alpha/2),
        "elo_upper": bootstrap_elo_df.quantile(1-alpha/2),
        "elo_std": bootstrap_elo_df.std()
    })

def bootstrap_pairwise_differences(bootstrap_df, alpha=0.05):
    systems = bootstrap_df.columns
    results = []

    for i, a in enumerate(systems):
        for b in systems[i+1:]:
            diff = bootstrap_df[a] - bootstrap_df[b]

            lower = diff.quantile(alpha/2)
            upper = diff.quantile(1-alpha/2)
            mean = diff.mean()

            results.append({
                "A": a,
                "B": b,
                "mean_diff": mean,
                "lower": lower,
                "upper": upper,
                "significant": not (lower <= 0 <= upper)
            })

    return pd.DataFrame(results).sort_values("mean_diff", ascending=False)


def plot_forest_elo(bootstrap_elo_ci, real_elo):
    """
    Creates a forest plot of Elo scores with 95% CI.
    """
    df_plot = bootstrap_elo_ci.copy()
    df_plot["real_elo"] = real_elo
    df_plot = df_plot.sort_values("real_elo", ascending=True)    
    plt.figure(figsize=(8, len(df_plot)*0.5))
    plt.errorbar(
        df_plot["real_elo"],
        df_plot.index,
        xerr=[df_plot["real_elo"] - df_plot["elo_lower"],
              df_plot["elo_upper"] - df_plot["real_elo"]],
        fmt='o',
        color='#ff8700',
        ecolor="#ffb056",
        elinewidth=2,
        capsize=4
    )
    plt.gca().set_facecolor("#2c2c2c")
    plt.axvline(x=1000, color="#D8D8D8", linestyle='--', label="Initial Elo")
    plt.xlabel("Elo score")
    plt.ylabel("Model")
    plt.title("Elo Scores and Standard Deviations")
    plt.tight_layout()
    plt.show()

plt.rcParams['text.usetex'] = True
plt.rcParams['font.family'] = 'Asana Math'
plt.rcParams['font.size'] = 12
# Read the Excel file
df = pd.read_excel("user_study_results.xlsx")

# Ensure timestamp is datetime
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Convert all columns to string for searching
df_str = df.astype(str)
# Identify rows containing "attentionCheck" in any column
attention_mask = df_str.apply(
    lambda row: row.str.contains("attentionCheck", case=False, na=False).any(),
    axis=1
)

# Identify rows that FAIL the attention check
failed_attention_mask = attention_mask & (df["choice"] != 2)

failed_attention_rows = df[failed_attention_mask]
print("\nFAILED ATTENTION CHECK ROWS (triggering full user removal):\n")
print(failed_attention_rows)

# Identify userIDs to remove entirely
bad_user_ids = failed_attention_rows["userID"].unique()

df_cleaned = df[~df["userID"].isin(bad_user_ids)]
df_cleaned = df_cleaned[~df_cleaned["responseCount"].isin([0, 1])] # Remove the example questions (question 1 and 2)

grouped = df_cleaned.groupby("userID")

df_filtered = grouped.filter(lambda x: len(x) >= 18) # remove people that did not finish the test

attention_mask = df_filtered.apply(
    lambda row: row.str.contains("attentionCheck", case=False, na=False).any(), # Remove the attention checks from the final dataframe
    axis=1
)

print("REMOVED INCOMPLETE RESULTS COUNT:\n")
print(len([x for x in attention_mask if x]))

df_filtered = df_filtered[(~attention_mask)]
filtered_grouped = df_filtered.groupby("userID")

# Count remaining attentionCheck rows per group
attention_check_counts = filtered_grouped.apply(
    lambda g: g.astype(str).apply(
        lambda row: row.str.contains("attentionCheck", case=False, na=False).any(),
        axis=1
    ).sum()
)

# gender counts and percentages
gender_counts = df_filtered["gender"].value_counts()
gender_percentages = gender_counts / len(df_filtered) * 100
print("\nGENDER COUNTS AND PERCENTAGES:\n")
print(gender_counts)
print(gender_percentages)

# language counts and percentages
language_counts = df_filtered["language"].value_counts()
language_percentages = language_counts / len(df_filtered) * 100
print("\nLANGUAGE COUNTS AND PERCENTAGES:\n")
print(language_counts)
print(language_percentages)

# average age and std
age_mean = df_filtered["age"].mean()
age_median = df_filtered["age"].median()
age_std = df_filtered["age"].std()
print("\nAGE MEAN AND STD:\n")
print(age_mean)
print(age_std)
print(age_median)

# counts of system appearance
counts = df_filtered["left"].value_counts() + df_filtered["right"].value_counts()
print("\nSYSTEM APPEARANCE COUNTS:\n")
print(counts)

print(f"number of people used in the anaylsis: {len(df_filtered['userID'].unique())}")
print(f"number of results used in the anaylsis: {len(df_filtered)}")
# ==========================================
# PAIRWISE RESULT MATRICES
# ==========================================

weak_matrix, strong_matrix, tie_matrix = pairwise_result_matrices(df_filtered)

print("\nWEAK WIN MATRIX:\n")
print(weak_matrix)

print("\nSTRONG WIN MATRIX:\n")
print(strong_matrix)

print("\nTIE MATRIX:\n")
print(tie_matrix)

elo_ranking = compute_mle_elo(df_filtered)
print("\ELO RANKING:\n")
print(elo_ranking)
win_rate = win_rate_split_ties(df_filtered)
print("\WIN RATES:\n")
print(win_rate)
if(os.path.exists("output/bootstrap_elo_lu.csv")):
    bootstrap_elo = pd.read_csv("output/bootstrap_elo_lu.csv", index_col=0)
else:
    bootstrap_elo = bootstrap_elo(df_filtered, 10000)
# PAIRWISE SIGNIFICANCE
print("\BOOTSTRAP ELO DIFFERENCES PAIRWISE SIGNIFICANCE:\n")
bootstrap_pairwise = bootstrap_pairwise_differences(bootstrap_elo, 1e-100)
print(bootstrap_pairwise)
bootstrap_elo_ci = bootstrap_elo_confidence_intervals(bootstrap_elo, 0.05)
print("\BOOTSTRAP ELO CONFIDENCE INTERVALS:\n")
print(bootstrap_elo_ci)
print("\BOOTSTRAP WIN RATE:\n")
if(os.path.exists("output/bootstrap_wr_lu.csv")):
    bootstrap_win_rate = pd.read_csv("output/bootstrap_wr_lu.csv", index_col=0)
else:
    bootstrap_win_rate = bootstrap_win_rate(df_filtered, 10000)
bootstrap_win_rate_ci = win_rate_confidence_intervals(bootstrap_win_rate, 0.05)
print(bootstrap_win_rate_ci)

plot_forest_elo(bootstrap_elo_ci, real_elo=elo_ranking)