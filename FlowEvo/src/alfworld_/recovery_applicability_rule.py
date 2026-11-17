"""Human applicability baseline. Never include this module in the S1 wire."""

import re

from .precondition_diagnostic import NOOP, command, receipt_effect
from .recovery_applicability import compatible, placement_goal


def check_rule(context):
    history = context['history']
    if not history or history[-1]['observation']!=NOOP:
        return 'DECLINE'
    failed = command(history[-1]['action'])
    if failed is None or failed[0]!='move':
        return 'DECLINE'
    if context['observation']!=NOOP:
        return 'UNKNOWN'
    goal = context['goal']
    if re.fullmatch(r'examine .+ with .+\.',goal.lower()):
        return 'DECLINE'
    parsed_goal = placement_goal(goal)
    if parsed_goal is None:
        return 'UNKNOWN'
    subject, target = failed[1]
    obj, destination, prerequisite = parsed_goal
    checks = (compatible(obj,subject),compatible(destination,target))
    if False in checks:
        return 'DECLINE'
    if None in checks or not subject.number or not target.number:
        return 'UNKNOWN'
    if prerequisite:
        confirmed = False
        for step in history[:-1]:
            parsed = command(step['action'])
            if parsed and parsed[0]==prerequisite and parsed[1][0]==subject:
                confirmed |= receipt_effect(parsed,step['observation'])=='TRUE'
        if not confirmed:
            return 'UNKNOWN'
    # A fresh explicit receipt must bind the closed state to this very instance.
    prior = next((step['observation'] for step in reversed(history[:-1])
                  if step['observation']!=NOOP), '')
    if not re.search(r'\bthe '+re.escape(target.name)+r' is closed\.',prior,re.IGNORECASE):
        return 'UNKNOWN'
    commands = context['admissible_commands']
    if 'open '+target.name not in commands:
        return 'DECLINE'
    if destination.number is None:
        for text in commands:
            parsed = command(text)
            if parsed and parsed[0]=='open' and parsed[1][0].category==target.category and parsed[1][0]!=target:
                return 'UNKNOWN'
    return 'MATCH'
