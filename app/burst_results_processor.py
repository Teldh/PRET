import pandas as pd

"""
Includes utility functions that are used to process burst results and obtain data for other applications.
"""


def find_average_len(burst_results) -> dict:
    """
    Finds the average length of bursts of a concept.

    :param bursts_results (pandas.DataFrame): df with these columns [keyword,level,start,end]
    :return avg (dict): dict with concepts associated to the average length of their bursts
    """
    avg = {}

    for t in burst_results["keyword"].unique().tolist():

        sub_df = burst_results.where(burst_results['keyword'] == t).dropna()
        tot_len = 0

        for i, r in sub_df.iterrows():
            tot_len += (sub_df.loc[i]["end"] - sub_df.loc[i]["start"]) + 1

        avg[t] = tot_len / sub_df.shape[0]

    return avg


def find_first_longest(burst_results, avg) -> dict:
    """
    Finds the first burst having a length that is higher than the average length of all bursts of that concept.

    :param bursts_results (pandas.DataFrame): df with these columns [keyword,level,start,end]
    :param avg (dict): average length of bursts of a concept

    :return: first_longest (dict): dictionary with concepts associated with the id of the first longest burst
    """
    first_longest = {}

    for t in burst_results["keyword"].unique().tolist():

        sub_df = burst_results.where(burst_results['keyword'] == t).dropna()

        for i, r in sub_df.iterrows():
            if sub_df.shape[0] == 1:
                first_longest[t] = i
            else:
                curr_len = sub_df.loc[i]["end"] - sub_df.loc[i]["start"] + 1
                if curr_len > avg[t]:
                    first_longest[t] = i
                    break

        if t not in first_longest:
            first_longest[t] = sub_df[burst_results["end"] - burst_results["start"] + 1 == avg[t]].iloc[0].name

    return first_longest


def get_json_with_bursts(burst_results, sents_idx):
    """Gets a list of bursts with first/last/ongoing/unique tags that can be uses for the gantt interface.

    :param bursts_results: pandas df with these columns [keyword,level,start,end]
    :param occ_index_file (str): name of the csv file containing the indexes of sentences
                                where every concept occurs. It must be a
                                tab separated file with the following columns:
                                "Lemma"    "idFrase"    "idParolaStart"
    :return: json with this format: {"startSent": 0, "endSent": 9, "concept": "computer", "ID": 1, "status": "FIRST"}
    """
    bursts_json = []

    '''sents_idx = pd.read_csv(occ_index_file, encoding="utf-8", index_col=None, sep="\t",
                          usecols=["Lemma", "idFrase", "idParolaStart"])'''


    # format: {"startSent": 0, "endSent": 9, "concept": "computer", "ID": 1, "freqOfTerm": 7, "status": "FIRST"}
    for i, row in burst_results.iterrows():
        curr_dict = {}
        curr_dict["startSent"] = int(row["start"])
        curr_dict["endSent"] = int(row["end"])
        curr_dict["concept"] = row["keyword"]
        curr_dict["ID"] = int(i)

        curr_dict["freqOfTerm"] = sents_idx[(sents_idx["idFrase"] >= int(row["start"])) &
                                            (sents_idx["idFrase"] <= int(row["end"])) &
                                            (sents_idx["Lemma"] == row["keyword"])].shape[0]

        if len(burst_results[burst_results["keyword"] == row["keyword"]]["start"]) == 1:
            curr_dict["status"] = "UNIQUE"
        elif row["start"] == burst_results[burst_results["keyword"] == row["keyword"]]["start"].min():
            curr_dict["status"] = "FIRST"
        elif row["end"] == burst_results[burst_results["keyword"] == row["keyword"]]["end"].max():
            curr_dict["status"] = "LAST"
        else:
            curr_dict["status"] = "ONGOING"

        bursts_json.append(curr_dict)

    return bursts_json


def give_direction_using_first_burst(undirected_matrix: pd.DataFrame,
                                     bursts_results: pd.DataFrame,
                                     indexes,
                                     level=1, preserve_relations=False) -> pd.DataFrame:
    """

    # If the matrix has not been processed averaging the weights, this procedure potentially kills too many relations!!!
    Choose preserve_relations=True in order to save relations.
    :param undirected_matrix:
    :param bursts_results:
    :param occ_index_file:
    :param level:
    :param preserve_relations: If False, the weight in the "wrong" direction is killed and the weight in
                            the right direction remains the same (potentially zero).
                            If True, before the weight in the "wrong" direction is killed,
                            the weight in the "right" direction is checked: if this is zero,
                            it will be replaced with the weight of the wrong direction (and then
                            the wrong is killed).
    :return: directed_df
    """
    filtered_bursts = bursts_results.where(bursts_results['level'] == level).dropna()
    '''indexes = pd.read_csv(occ_index_file, encoding="utf-8", index_col=0, sep="\t",
                          usecols=["Lemma", "idFrase", "idParolaStart"])'''

    directed_df = undirected_matrix.copy()

    for t1 in directed_df.index.tolist():

        other_terms = directed_df.index.tolist()
        other_terms.remove(t1)

        for t2 in other_terms:

            start_first_burst_t1 = filtered_bursts[filtered_bursts["keyword"] == t1].iloc[0]["start"]
            start_first_burst_t2 = filtered_bursts[filtered_bursts["keyword"] == t2].iloc[0]["start"]

            if start_first_burst_t1 < start_first_burst_t2:
                # t1 is a prereq of t2
                if preserve_relations and directed_df.at[t1, t2] == 0:
                    directed_df.at[t1, t2] = directed_df.at[t2, t1]
                directed_df.at[t2, t1] = 0
            elif start_first_burst_t2 < start_first_burst_t1:
                # t2 is a prereq of t1
                if preserve_relations and directed_df.at[t2, t1] == 0:
                    directed_df.at[t2, t1] = directed_df.at[t1, t2]
                directed_df.at[t1, t2] = 0
            elif start_first_burst_t2 == start_first_burst_t1:
                # they are in the same sentence: need to check the tokens
                #t1_pos_in_sent = indexes[indexes["idFrase"] == start_first_burst_t1].loc[t1]["idParolaStart"].min()
                #t2_pos_in_sent = indexes[indexes["idFrase"] == start_first_burst_t1].loc[t2]["idParolaStart"].min()

                t1_pos_in_sent = indexes[indexes["idFrase"] == start_first_burst_t1].loc[indexes["Lemma"] == t1]["idParolaStart"].min()
                t2_pos_in_sent = indexes[indexes["idFrase"] == start_first_burst_t1].loc[indexes["Lemma"] == t2]["idParolaStart"].min()

                if t1_pos_in_sent < t2_pos_in_sent:
                    # t1 is a prereq of t2
                    if preserve_relations and directed_df.at[t1, t2] == 0:
                        directed_df.at[t1, t2] = directed_df.at[t2, t1]
                    directed_df.at[t2, t1] = 0
                elif t2_pos_in_sent < t1_pos_in_sent:
                    # t2 is a prereq of t1
                    if preserve_relations and directed_df.at[t2, t1] == 0:
                        directed_df.at[t2, t1] = directed_df.at[t1, t2]
                    directed_df.at[t1, t2] = 0
                else:
                    # the two concepts are an embedding concept and its nested concept:
                    # use length to decide direction (the one with less words is the prerequisite)
                    if len(t1.split()) < len(t2.split()):
                        directed_df.at[t2, t1] = 0
                    elif len(t2.split()) < len(t1.split()):
                        directed_df.at[t1, t2] = 0
                    else:
                        print("Impossible to give direction to this pair (not even by "
                              "looking at the first sentence of their first burst):", t1, "\t", t2)
            else:
                print("Impossible to give direction to:", t1, "\t<->\t", t2)

    directed_df = directed_df.round(decimals=3)

    return directed_df


def to_edgelist(df):
    edges = []
    for i in df.index.tolist():
        for c in df.columns.tolist():
            edges.append((i, c, df.loc[i][c]))

    edges_sorted = sorted(edges, key=lambda edges: edges[2], reverse=True)
    return edges_sorted
