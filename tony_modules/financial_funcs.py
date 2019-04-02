import re
from pydot import Dot, Edge
from collections import namedtuple


class Debt:

    def __init__(self, owed_to, owed_by, amount):
        self.owed_to = owed_to
        self.owed_by = owed_by
        self.amount = amount

    def __str__(self):
        return f"{self.owed_by} owes {self.owed_to} ${self.amount}"


################################### Debt Collection Operations #############################################
  
#algorithm taken from https://stackoverflow.com/questions/15723165/algorithm-to-simplify-a-weighted-directed-graph-of-debts
#basically total credit = total debt and all that matters is each person either recieves some amount of money or pays some amount of money
#so anyone with debt can pay anyone who's owed money and it all works out
def reduce(debts):
    totals = sum_debts(debts)
    Payment = namedtuple('Payment', ['person', 'amount'])
    credit = [Payment(person, amt) for person, amt in totals.items() if amt > 0]
    debt = (Payment(person, -amt) for person, amt in totals.items() if amt < 0)
    new_debts = []
    for debt_payment in debt:
        credit_payment = credit[0]
        while credit_payment.amount < debt_payment.amount: #keep paying people off until debt person can no longer completely pay them off
            transaction = Debt(credit_payment.person, debt_payment.person, credit_payment.amount)
            new_debts.append(transaction)
            remaining_debt = round(debt_payment.amount - transaction.amount, 5) #round to 5 digits so floating point math doesn't mess this loop up
            debt_payment = Payment(debt_payment.person, remaining_debt)
            credit.pop(0)
            credit_payment = credit[0]
        last_transaction = Debt(credit_payment.person, debt_payment.person, debt_payment.amount) #give last bit of debt payment to the next credit owner
        new_debts.append(last_transaction)
        remaining_credit = round(credit_payment.amount - last_transaction.amount, 2)
        credit[0] = Payment(credit_payment.person, remaining_credit)
    return new_debts

def sum_debts(debts):
    totals = {}
    for d in debts:
        debt = totals.get(d.owed_by, 0)
        totals[d.owed_by] = round(debt - d.amount, 5) #round to 5 digits because floating point errors are ugly but we wanna be precise still
        credit = totals.get(d.owed_to, 0)
        totals[d.owed_to] = round(credit + d.amount, 5)
    return totals

def plot_debts(all_debts, file_path):
    graph = Dot()
    for debt in all_debts:
        amt_str = '$' + str(round(debt.amount, 2)) #round to cents when we display everything
        new_edge = Edge(debt.owed_to, debt.owed_by, label = amt_str)
        graph.add_edge(new_edge)
    graph.write_png(file_path)


################################### Message parsing #############################################
 
DEBT_QUERY = re.compile(r'(.+)owes?(.+)')
MONEY_QUERY = re.compile(r'\$[\d.]+|[\d.]+\$|[\d.]+ dollars|[\d.]+ bucks')
NAMES = {
    'ehren': 'Ehren',
    'wak': 'Ehren',
    '<@137749893207949312>': 'Ehren',
    'daniel': 'Daniel',
    'noid': 'Daniel',
    '<@309781352671084554>': 'Daniel',
    'aidan': 'Aidan',
    'lego': 'Aidan',
    '<@338163863738646528>': 'Aidan',
    'sam': 'Sam',
    '<@338139208621490177>': 'Sam',
    'julien': 'Julien',
    '<@165576756525400065>': 'Julien'
}
 
def parse_message(message):
    names = NAMES.copy()
    name_query_string = r'|'.join(names) + r'|\bi\b|\bme\b' #query to find all names, also add in matches for "me" and "I"
    name_query = re.compile(name_query_string)
    user_id = "<@{}>".format(message.author.id)
    names['i'] = names[message.author.user] #so we can convert back from "I" and "me" later
    names['me'] = names[message.user]
    message = message.text.lower()
    parsed_debts = []
    for msg in message.split('\n'):
        debt_strs = DEBT_QUERY.search(msg)
        if debt_strs is not None:
            debt_holders = debt_strs.group(1)
            debt_holders = name_query.findall(debt_holders) #people who owe money
            loaners_and_money = debt_strs.group(2)
            loan_sharks = name_query.findall(loaners_and_money) #people who money was borrowed from
            money_exchanged = MONEY_QUERY.search(loaners_and_money)
            if money_exchanged is not None:
                money_exchanged = re.search(r'[\d.]+', money_exchanged.group()).group() #get just the number
                money_exchanged = float(money_exchanged)
                for payer in debt_holders: #don't have to check that theres no debt holders or no loan sharks since findall always returns a list
                    for reciever in loan_sharks:
                        if payer in names and reciever in names:
                            new_debt = Debt(names[reciever], names[payer], money_exchanged)
                            parsed_debts.append(new_debt)
    return parsed_debts


################################### Discord Integration #############################################

class Financials:

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def iou(self, ctx, *args):
        all_ious = GET EM
        all_debts = []
        for iou in all_ious:
            parsed_ious = parse_message(iou)
            for debt in parsed_ious:
                all_debts.apped(debt)
                if 'quiet' not in args:
                    await ctx.send(debt)
        plot_debts(all_debts, 'debt_plot.png')
        await ctx.send()
        original_sum = sum_debts(all_debts)
        debts = reduce(all_debts)
        plot_debts(all_debts, 'C:\\Users\\Wakydawgster\\Desktop\\delpls2.png')
        final_sum = sum_debts(debts)
        if final_sum == original_sum:
            print("Check: Successful:white_check_mark: (Reduced debt sums equal original debt sums)")
        else:
            print("ERROR: REDUCED DEBT SUMS DON'T EQUAL ORIGINAL DEBT SUMS! (might just be floating point math error but I thought I got rid of all those)")
            print(f"original sums: {original_sum}")
            print(f"reduced sums: {final_sum}")
        balances_string = ''.join(f"\n    {name}: {balance}" for name, balance in final_sum.items())
        print("Balances:" + balances_string)
        total_debt_string = str(sum(balance for balance in final_sum.values() if balance > 0))
        print("Total debt: " + total_debt_string)
            

def setup(bot):
    bot.add_cog(WakFuncs(bot))
    bot.wstorage = WakStore()
    bot.loop.create_task(background(bot))


################################### Testing #############################################

if __name__ == "__main__":
    debts = [
        Debt('Ehren', 'Sam', 7.5),
        Debt('Ehren', 'Daniel', 6),
        Debt('Ehren', 'Julien', 15),
        Debt('Ehren', 'Julien', 0.1),
        Debt('Ehren', 'Aidan', 1.5),
        Debt('Daniel', 'Aidan', 9),
        Debt('Daniel', 'Julien', 15),
        Debt('Aidan', 'Julien', 20),
        Debt('Aidan', 'Sam', 7.5),
        Debt('Julien', 'Sam', 7.5),
        Debt('Sam', 'Ehren', 12.5),
        Debt('Sam', 'Ehren', 6.45),
        Debt('Sam', 'Ehren', 20),
        Debt('Julien', 'Ehren', 14),
        Debt('Sam', 'Ehren', 14),
        Debt('Aidan', 'Ehren', 14)
    ]
    plot_debts(debts, 'C:\\Users\\Wakydawgster\\Desktop\\delpls.png')
    original_sum = sum_debts(debts)
    debts = reduce(debts)
    plot_debts(debts, 'C:\\Users\\Wakydawgster\\Desktop\\delpls2.png')
    final_sum = sum_debts(debts)
    if final_sum == original_sum:
        print("Check: Successful:white_check_mark: (Reduced debt sums equal original debt sums)")
    else:
        print("ERROR: REDUCED DEBT SUMS DON'T EQUAL ORIGINAL DEBT SUMS! (might just be floating point math error but I thought I got rid of all those)")
        print(f"original sums: {original_sum}")
        print(f"reduced sums: {final_sum}")
    balances_string = ''.join(f"\n    {name}: {balance}" for name, balance in final_sum.items())
    print("Balances:" + balances_string)
    total_debt_string = str(sum(balance for balance in final_sum.values() if balance > 0))
    print("Total debt: " + total_debt_string)

    
    Msg = namedtuple('Msg', ['text', 'user'])
    parsed = parse_message(Msg('jolly owes me like 13 bucks', 'ehren'))
    #parsed = parse_message(Msg('Aidan, sam, and Julien owe ehren $14', 'ehren'))
    for p in parsed:
        print(p)
