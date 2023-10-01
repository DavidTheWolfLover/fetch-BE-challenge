from typing import Optional
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json

#Intialize the RESTAPI through FastAPI()
app = FastAPI()

#Initialize Transaction class
class Transaction(BaseModel):
    id: Optional[int] = None
    payer : str
    points : int
    timestamp : str

#Intialize transaction.json and importing previous transactions and balances
with open("transaction.json") as f:
    table = json.load(f)
    transactions = table["transaction"]
    balances = table["balance"]

#Accepts a transaction which contains
#how many points will be added, what payer the points will be added through, and the timestamp for when the
#transaction takes place. 
@app.post("/add", status_code=200)
def add_transaction(trans: Transaction):
    #get the latest id
    t_id = max([t["id"] for t in transactions], default = 0) + 1

    #appending new transaction to current transactions list
    new_trans = {
        "id" : t_id,
        "payer" : trans.payer,
        "points" : trans.points,
        "timestamp" : trans.timestamp,
        "afterpay points": trans.points
    }
    transactions.append(new_trans)

    #adding points to payer's balances
    payer = next((b for b in balances if b["payer"] == trans.payer), None)
    if payer is not None: #check if payer intialized before or not
        payer["points"] += trans.points
    else:
        new_user = {
            "payer" : trans.payer,
            "points" : trans.points
        }
        balances.append(new_user)

    #update the transaction.json
    with open("transaction.json", "w") as f:
        json.dump(table, f)
    
    #return the updated json
    return table

@app.post("/spend", status_code=200)
def spend_points(points: int = 0):
    #Sort the transactions by timestamp
    global transactions
    transactions = sorted(transactions, key=lambda x: x["timestamp"])
    #No. points to be deducted
    paypoints = points
    #Dict containing users that get points deducted
    balance_change = {}
    total_points = sum([x["points"] for x in transactions])

    #Throw error 400 if a request was made to spend more points than what a user has in total
    if total_points < points:
        return JSONResponse(
            status_code=400,
            content="User doesnt have enough points",
        )
    #Deduct points from each transaction
    for x in transactions:
        if x["afterpay points"] == 0:
            continue 

        if paypoints <= x["afterpay points"]:
            x["afterpay points"] -= paypoints
            balance_change[x["payer"]] = balance_change.get(x["payer"], 0) - paypoints
            break
        else:
            paypoints -= x["afterpay points"]
            balance_change[x["payer"]] = balance_change.get(x["payer"], 0) - x["afterpay points"]
            x["afterpay points"] = 0

    #Converting dict to output json
    output = []
    for key, value in balance_change.items():
        user_info = {
            "payer": key,
            "points": value
        }
        #Remove points from payer's balances
        payer = next((b for b in balances if b["payer"] == key), None)
        payer["points"] += value # value are negative

        #update the transaction.json
        with open("transaction.json", "w") as f:
            json.dump(table, f)

        output.append(user_info)
    return output

#Return a map of points the user has in their account based on the payer they were
#added through
@app.get('/balance', status_code=200)
def get_balance():
    all_balance = {b["payer"]: b["points"] for b in balances}
    return all_balance

