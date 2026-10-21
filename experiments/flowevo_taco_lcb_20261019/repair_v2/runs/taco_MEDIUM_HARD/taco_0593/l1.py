def count_change(money, coins):
    if money < 0:
        return 0

    dp = [0] * (money + 1)
    dp[0] = 1

    for coin in coins:
        if coin <= 0:
            continue
        for amount in range(coin, money + 1):
            dp[amount] += dp[amount - coin]

    return dp[money]