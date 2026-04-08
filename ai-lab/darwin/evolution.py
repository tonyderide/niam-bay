"""Darwinian evolution: select, crossover, mutate."""
import random
import uuid
from agent import Agent, SKILL_POOL

def select_survivors(agents: list[Agent], kill_ratio: float = 0.3) -> list[Agent]:
    """Sort by fitness, kill the bottom kill_ratio. Return survivors."""
    ranked = sorted(agents, key=lambda a: a.fitness, reverse=True)
    cut = max(2, int(len(ranked) * (1 - kill_ratio)))
    survivors = ranked[:cut]
    for a in ranked[cut:]:
        a.alive = False
    return survivors

def crossover(parent1: Agent, parent2: Agent, generation: int) -> Agent:
    """Combine skills from two parents. Each skill has 50% chance from each parent."""
    all_skills = {}
    for name, weight in parent1.skills.items():
        if random.random() < 0.5:
            all_skills[name] = weight
    for name, weight in parent2.skills.items():
        if name not in all_skills and random.random() < 0.5:
            all_skills[name] = weight
    if not all_skills:
        donor = random.choice([parent1, parent2])
        name = random.choice(list(donor.skills.keys()))
        all_skills[name] = donor.skills[name]
    return Agent(
        agent_id=f"agent-{uuid.uuid4().hex[:6]}",
        skills=all_skills,
        generation=generation,
        parent_ids=[parent1.agent_id, parent2.agent_id],
    )

def mutate(agent: Agent, rate: float = 0.3) -> Agent:
    """Mutate an agent's skills: add, remove, or tweak weights."""
    new_skills = dict(agent.skills)
    pool = list(SKILL_POOL.keys())

    for skill_name in list(new_skills.keys()):
        if random.random() < rate:
            action = random.choice(["tweak", "remove", "replace"])
            if action == "tweak":
                new_skills[skill_name] = max(0.1, min(1.0, new_skills[skill_name] + random.uniform(-0.2, 0.2)))
            elif action == "remove" and len(new_skills) > 1:
                del new_skills[skill_name]
            elif action == "replace":
                new_name = random.choice(pool)
                if new_name not in new_skills:
                    del new_skills[skill_name]
                    new_skills[new_name] = round(random.uniform(0.3, 1.0), 2)

    if random.random() < rate:
        new_name = random.choice(pool)
        if new_name not in new_skills:
            new_skills[new_name] = round(random.uniform(0.3, 1.0), 2)

    agent.skills = new_skills
    return agent

def evolve_generation(agents: list[Agent], target_size: int, kill_ratio: float = 0.3, mutation_rate: float = 0.3) -> list[Agent]:
    """One full evolution cycle: select -> reproduce -> mutate."""
    survivors = select_survivors(agents, kill_ratio)
    next_gen = []

    for s in survivors:
        s.generation += 1
        mutate(s, rate=mutation_rate * 0.5)
        next_gen.append(s)

    while len(next_gen) < target_size:
        p1, p2 = random.sample(survivors, min(2, len(survivors)))
        child = crossover(p1, p2, generation=survivors[0].generation)
        mutate(child, rate=mutation_rate)
        next_gen.append(child)

    return next_gen[:target_size]
