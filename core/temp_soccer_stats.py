import json

# Load all bets
with open('/Users/dickgibbons/betting_data/bet_history.json', 'r') as f:
    all_bets = json.load(f)

# Filter SOCCER bets (all caps)
soccer_bets = [bet for bet in all_bets if bet.get('sport') == 'SOCCER']

# Calculate stats
total = len(soccer_bets)
wins = sum(1 for bet in soccer_bets if bet.get('result') == 'W')
losses = sum(1 for bet in soccer_bets if bet.get('result') == 'L')
pushes = sum(1 for bet in soccer_bets if bet.get('result') == 'P')
pending = sum(1 for bet in soccer_bets if bet.get('result') == 'pending')

profit = sum(bet.get('profit', 0) for bet in soccer_bets if bet.get('profit') is not None)
win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

print(f'⚽ SOCCER BETTING PERFORMANCE')
print(f'=' * 50)
print(f'Total Bets: {total}')
print(f'Record: {wins}-{losses}-{pushes}')
print(f'Win Rate: {win_rate:.1f}%')
print(f'Profit/Loss: ${profit:,.2f}')
print(f'Pending: {pending}')
print()

# Break down by confidence
by_confidence = {}
for bet in soccer_bets:
    conf = bet.get('confidence', 'UNKNOWN')
    if conf not in by_confidence:
        by_confidence[conf] = {'wins': 0, 'losses': 0, 'profit': 0, 'pending': 0}

    if bet.get('result') == 'W':
        by_confidence[conf]['wins'] += 1
    elif bet.get('result') == 'L':
        by_confidence[conf]['losses'] += 1
    elif bet.get('result') == 'pending':
        by_confidence[conf]['pending'] += 1

    if bet.get('profit') is not None:
        by_confidence[conf]['profit'] += bet['profit']

if by_confidence:
    print('BY CONFIDENCE LEVEL:')
    for conf in ['ELITE', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']:
        if conf in by_confidence:
            stats = by_confidence[conf]
            total_bets = stats['wins'] + stats['losses']
            wr = (stats['wins'] / total_bets * 100) if total_bets > 0 else 0
            print(f'  {conf}: {stats["wins"]}-{stats["losses"]} ({wr:.1f}%) | ${stats["profit"]:,.2f} | Pending: {stats["pending"]}')

# Most recent soccer bets
print(f'\nMOST RECENT SOCCER BETS:')
recent_soccer = [bet for bet in soccer_bets if bet.get('result') != 'pending'][-5:]
for bet in recent_soccer:
    result_emoji = '✅' if bet['result'] == 'W' else '❌'
    profit_val = bet.get('profit', 0)
    profit_str = f'+${profit_val:.2f}' if profit_val > 0 else f'${profit_val:.2f}'
    bet_text = bet.get('bet', 'N/A')[:50]
    print(f'  {result_emoji} {bet.get("date")} | {bet_text} | {profit_str}')
