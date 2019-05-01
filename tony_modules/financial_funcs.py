import re
import io
from pydot import Dot, Edge
from collections import namedtuple
from discord.ext import commands
import discord


class Debt:

    def __init__(self, owed_to, owed_by, amount):
        self.owed_to = owed_to
        self.owed_by = owed_by
        self.amount = amount
        self.normalize()

    def __str__(self):
        return f"{self.owed_by} owes {self.owed_to} ${self.amount}"

    def __add__(self, other_debt):
        if {other_debt.owed_to, other_debt.owed_by} != {self.owed_to, self.owed_by}:
            raise ValueError("Only Debts between the same parties can be added together")
        debt_sum = Debt(self.owed_to, self.owed_by, other_debt.amount)
        if other_debt.owed_to == self.owed_by: #if owed to and owed by are reversed, then other_debt's amount is actually negative relative to self's amount
            debt_sum.amount = -debt_sum.amount
        debt_sum.amount += self.amount
        debt_sum.normalize()
        debt_sum.amount = round(debt_sum.amount, 5) #avoid float errors
        return debt_sum

    def normalize(self):
        "if amount is negative: swap owed_to and owed_by and make amount positive"
        if self.amount < 0:
            temp_owed_to = self.owed_to
            self.owed_to = self.owed_by
            self.owed_by = temp_owed_to
            self.amount = -self.amount
        

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

#similar to reduce, but combines vertices that are to the same nodes
def simplify(debts):
    simplified = {}
    for d in debts:
        parties = frozenset((d.owed_to, d.owed_by)) #use frozenset so I can use it as keys for simplified
        default_debt = Debt(d.owed_to, d.owed_by, 0)
        summed_debt = simplified.get(parties, default_debt)
        summed_debt += d
        simplified[parties] = summed_debt
    return list(simplified.values())

def sum_debts(debts):
    totals = {}
    for d in debts:
        debt = totals.get(d.owed_by, 0)
        totals[d.owed_by] = round(debt - d.amount, 5) #round to 5 digits because floating point errors are ugly but we wanna be precise still
        credit = totals.get(d.owed_to, 0)
        totals[d.owed_to] = round(credit + d.amount, 5)
    totals = {name: tot for name, tot in totals.items() if tot != 0} #get rid of totals that equal 0
    return totals

def plot_debts(all_debts):
    graph = Dot()
    for debt in all_debts:
        amt_str = '$' + str(round(debt.amount, 2)) #round to cents when we display everything
        new_edge = Edge(debt.owed_by, debt.owed_to, label = amt_str)
        graph.add_edge(new_edge)
    return graph.create_png()


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

async def plot_and_send(ctx, debts, additional_text):
    graph = plot_debts(debts) 
    graph = discord.File(io.BytesIO(graph), filename = "ious.png")
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
        simplified_debts = simplify(all_debts)
        await plot_and_send(ctx, simplified_debts, "Simplified IOU graph:")
        simplified_sum = sum_debts(simplified_debts)
        all_debts = reduce(all_debts)
        await plot_and_send(ctx, all_debts, "Fully reduced IOU graph:")
        final_sum = sum_debts(all_debts)
        if final_sum == original_sum and simplified_sum == original_sum: #check to see if reduced graph is valid
            await ctx.send("Check: Successful :white_check_mark: (reduced/simplified debt sums equal original debt sums)")
        else:
            await ctx.send("**ERROR: REDUCED DEBT SUMS DON'T EQUAL ORIGINAL DEBT SUMS!** (might just be floating point math error but I thought I got rid of all those)")
            await ctx.send(f"original sums: {original_sum}")
            await ctx.send(f"simplified sums: {simplified_sum}")
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
