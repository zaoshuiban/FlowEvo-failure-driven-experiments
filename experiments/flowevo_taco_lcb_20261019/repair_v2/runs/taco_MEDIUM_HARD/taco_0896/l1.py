import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    n = next(it)
    m = next(it)
    k = next(it)

    arrivals = []
    departures = []
    max_day = 0

    for _ in range(m):
        d = next(it)
        f = next(it)
        t = next(it)
        c = next(it)

        if d > max_day:
            max_day = d

        if t == 0:
            arrivals.append((d, f, c))
        else:
            departures.append((d, t, c))

    INF = 10**18

    arrivals.sort()
    departures.sort(reverse=True)

    # pref[day] = minimum cost to bring all people to city 0
    # using only flights on days <= day.
    pref = [INF] * (max_day + 1)
    min_arrival = [INF] * (n + 1)

    arrived_count = 0
    arrival_cost = 0
    p = 0
    arrivals_len = len(arrivals)

    for day in range(max_day + 1):
        while p < arrivals_len and arrivals[p][0] == day:
            _, city, cost = arrivals[p]

            old_cost = min_arrival[city]
            if cost < old_cost:
                if old_cost == INF:
                    arrived_count += 1
                else:
                    arrival_cost -= old_cost

                min_arrival[city] = cost
                arrival_cost += cost

            p += 1

        if arrived_count == n:
            pref[day] = arrival_cost

    # Process departures backwards.
    min_departure = [INF] * (n + 1)

    departed_count = 0
    departure_cost = 0
    q = 0
    departures_len = len(departures)

    answer = INF

    for day in range(max_day, -1, -1):
        while q < departures_len and departures[q][0] == day:
            _, city, cost = departures[q]

            old_cost = min_departure[city]
            if cost < old_cost:
                if old_cost == INF:
                    departed_count += 1
                else:
                    departure_cost -= old_cost

                min_departure[city] = cost
                departure_cost += cost

            q += 1

        if departed_count == n:
            # If everyone has arrived by arrival_day, they can work for k days
            # only if departure day >= arrival_day + k + 1.
            arrival_day = day - k - 1

            if 0 <= arrival_day <= max_day:
                if pref[arrival_day] != INF:
                    total = pref[arrival_day] + departure_cost
                    if total < answer:
                        answer = total

    print(answer if answer != INF else -1)


if __name__ == "__main__":
    solve()