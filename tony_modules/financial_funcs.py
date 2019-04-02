import re
from pydot import Dot, Edge
from collections import namedtuple
from discord.ext import commands
import discord


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
        new_edge = Edge(debt.owed_by, debt.owed_to, label = amt_str)
        graph.add_edge(new_edge)
    graph.write_png(file_path)


################################### Message parsing #############################################
 
DEBT_QUERY = re.compile(r'(.+)owes?(.+)') #to find IOUs
MONEY_QUERY = re.compile(r'\$[\d.]+|[\d.]+\$|[\d.]+ dollars|[\d.]+ bucks') #to find monetary values
CROSSED_OUT_QUERY = re.compile(r'~+.*?~+') #to find crossed out text 
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
    names['i'] = names[user_id] #so we can convert back from "I" and "me" later
    names['me'] = names[user_id]
    message = message.content.lower()
    message = CROSSED_OUT_QUERY.sub('', message) #remove crossed out text (so crossed out ious are ignored)
    parsed_debts = []
    for msg in message.split('\n'):
        debt_strs = DEBT_QUERY.search(msg) #find all ious
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

IOU_CHANNEL_ID = 391842582948216833
GRAPH_PATH = "iou_graph.png"

async def plot_and_send(ctx, debts, additional_text):
    plot_debts(debts, GRAPH_PATH)
    graph = discord.File(GRAPH_PATH, filename = "ious.png")
    await ctx.send(additional_text, file = graph) #technically "dangerous" (since another call to !iou could change the file before it's sent) but it doesn't really matter for this command 

	
class Financials:

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def iou(self, ctx, *args):
        quiet = "quiet" in args
        if not quiet:
            await ctx.send("Parsing IOU channel... (use `!iou quiet` to hide IOU parsing output)")
        all_debts = await self.parse_discord_debts(ctx, quiet)
        await plot_and_send(ctx, all_debts, "Current IOUs visualized:")
        original_sum = sum_debts(all_debts)
        all_debts = reduce(all_debts)
        await plot_and_send(ctx, all_debts, "Reduced IOU graph:")
        final_sum = sum_debts(all_debts)
        if final_sum == original_sum: #check to see if reduced graph is valid
            await ctx.send("Check: Successful :white_check_mark: (Reduced debt sums equal original debt sums)")
        else:
            await ctx.send("**ERROR: REDUCED DEBT SUMS DON'T EQUAL ORIGINAL DEBT SUMS!** (might just be floating point math error but I thought I got rid of all those)")
            await ctx.send(f"original sums: {original_sum}")
            await ctx.send(f"reduced sums: {final_sum}")
        balances_string = ''.join(f"\n    {name}: {balance}" for name, balance in final_sum.items())
        await ctx.send("Balances:" + balances_string)
        total_debt = sum(balance for balance in final_sum.values() if balance > 0)
        await ctx.send(f"Total debt: **${total_debt}**")
    
    async def parse_discord_debts(self, ctx, quiet = False):
        iou_channel = self.bot.get_channel(IOU_CHANNEL_ID)
        all_debts = []
        async for iou in iou_channel.history(): 
            parsed_ious = parse_message(iou)
            all_debts += parsed_ious
            if not quiet: #send parsing information back to discord
                parse_str = f"```Original -> {iou.author.display_name}: {iou.content}"
                parsed_iou_strs = [str(i) for i in parsed_ious]
                parse_str += f"\nParsed -> {parsed_iou_strs}```"
                await ctx.send(parse_str)
        return all_debts
                        

def setup(bot):
    bot.add_cog(Financials(bot))


################################### Testing #############################################

if __name__ == "__main__":
    debts = [
        Debt('Sam', 'Ehren', 7.5),
        Debt('Daniel', 'Ehren', 6),
        Debt('Julien', 'Ehren', 15),
        Debt('Julien', 'Ehren', 0.1),
        Debt('Aidan', 'Ehren', 1.5),
        Debt('Aidan', 'Daniel', 9),
        Debt('Julien', 'Daniel', 15),
        Debt('Julien', 'Aidan', 20),
        Debt('Sam', 'Aidan', 7.5),
        Debt('Sam', 'Julien', 7.5),
        Debt('Ehren', 'Sam', 12.5),
        Debt('Ehren', 'Sam', 6.45),
        Debt('Ehren', 'Sam', 20),
        Debt('Ehren', 'Julien', 14),
        Debt('Ehren', 'Sam', 14),
        Debt('Ehren', 'Aidan', 14)
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
