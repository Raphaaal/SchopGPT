import concurrent.futures
import json
from pathlib import Path

from backend.tree import process_debate

HISTORIES = Path(__file__).parent / "histories.json"
DEBATE_RESULTS = Path(__file__).parents[1] / "backend" / "debate_results.json"


def main():
    with open(HISTORIES) as f:
        histories_data = json.load(f)

    flat_list = []
    for i, hist_d in enumerate(histories_data):
        for j, (k, v) in enumerate(hist_d.items()):
            new_hist = {i*10 + j: v}
            flat_list.append(new_hist)

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        results = list(executor.map(process_debate, flat_list))

    with open(DEBATE_RESULTS, "w") as f_out:
        json.dump(results, f_out)


if __name__ == "__main__":
    main()
