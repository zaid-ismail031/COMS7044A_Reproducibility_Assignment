from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path

TOKEN_RE = re.compile(r"[()]|[^\s()]+")


def parse(text):
    tokens = iter(TOKEN_RE.findall(re.sub(r";[^\n]*", "", text)))

    def read(token):
        if token != "(":
            return token
        result = []
        for next_token in tokens:
            if next_token == ")":
                return result
            result.append(read(next_token))
        raise ValueError("unterminated list")

    return read(next(tokens))


def render(node):
    if isinstance(node, str):
        return node
    return "(" + " ".join(render(child) for child in node) + ")"


def render_top(tree):
    body = "\n  ".join(render(child) for child in tree[1:])
    return f"({tree[0]}\n  {body}\n)"


def find(tree, key):
    for item in tree:
        if (
            isinstance(item, list)
            and item
            and isinstance(item[0], str)
            and item[0].lower() == key
        ):
            return item
    return None


def substitute(node, mapping):
    if isinstance(node, str):
        return mapping.get(node, node)
    return [substitute(child, mapping) for child in node]


def wrap_and(formula, extra):
    if isinstance(formula, list) and formula and formula[0] == "and":
        return ["and", *formula[1:], *extra]
    return ["and", formula, *extra]


def compile_problem(domain_text, problem_text, observations, *, non_compliant):
    domain = parse(domain_text)
    problem = parse(problem_text)
    m = len(observations)
    obs = [f"obs_{i}" for i in range(m + 1)]

    find(domain, ":predicates").extend([fluent] for fluent in obs)

    problem_objects = find(problem, ":objects")
    if problem_objects is not None and len(problem_objects) > 1:
        domain_constants = find(domain, ":constants")
        if domain_constants is None:
            domain_constants = [":constants"]
            insert_at = 2
            for idx, item in enumerate(domain):
                if isinstance(item, list) and item and isinstance(item[0], str) \
                        and item[0].lower() in (":requirements", ":types"):
                    insert_at = idx + 1
            domain.insert(insert_at, domain_constants)
        domain_constants.extend(problem_objects[1:])
        del problem_objects[1:]

    for i, (name, args) in enumerate(observations, start=1):
        original = next(
            action for action in domain
            if isinstance(action, list) and action
            and isinstance(action[0], str) and action[0].lower() == ":action"
            and action[1].lower() == name.lower()
        )
        params_value = original[original.index(":parameters") + 1]
        params = [t for t in params_value if isinstance(t, str) and t.startswith("?")]
        mapping = dict(zip(params, args))
        clone = [substitute(child, mapping) for child in original]
        clone[1] = f"{original[1]}__obs{i}"
        clone[clone.index(":parameters") + 1] = []
        pre = clone.index(":precondition") + 1
        eff = clone.index(":effect") + 1
        clone[pre] = wrap_and(clone[pre], [[obs[i - 1]]])
        clone[eff] = wrap_and(clone[eff], [[obs[i]]])
        domain.append(clone)

    if non_compliant:
        reqs = find(domain, ":requirements")
        if reqs is None:
            reqs = [":requirements"]
            domain.insert(2, reqs)
        if ":negative-preconditions" not in reqs:
            reqs.append(":negative-preconditions")

    find(problem, ":init").append([obs[0]])
    goal = find(problem, ":goal")
    target = ["not", [obs[m]]] if non_compliant else [obs[m]]
    goal[1] = wrap_and(goal[1], [target])

    return render_top(domain), render_top(problem)


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("domain", type=Path)
    parser.add_argument("problem", type=Path)
    parser.add_argument("observations")
    parser.add_argument("--tag", default="g")
    args = parser.parse_args(argv)

    observations = [(name, tuple(a)) for name, a in json.loads(args.observations)]
    domain_text = args.domain.read_text(encoding="utf-8")
    problem_text = args.problem.read_text(encoding="utf-8")

    out_dir = args.domain.parent
    for label, flag in (("compliant", False), ("non_compliant", True)):
        compiled_domain, compiled_problem = compile_problem(
            domain_text, problem_text, observations, non_compliant=flag
        )
        (out_dir / f"domain_{args.tag}_{label}.pddl").write_text(compiled_domain, encoding="utf-8")
        (out_dir / f"problem_{args.tag}_{label}.pddl").write_text(compiled_problem, encoding="utf-8")
        print(f"wrote {label} files for tag={args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
