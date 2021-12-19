import sys
import csv
import json
import time
from datetime import timedelta

from web3 import Web3

w3 = Web3(Web3.HTTPProvider('http://192.168.1.104:8545/'))

with open('uniswapv3abi.json') as f:
        abi = json.load(f)

UNISWAP_V3_ADDRESS = '0xE592427A0AEce92De3Edee1F18E0157C05861564'
contract = w3.eth.contract(address=UNISWAP_V3_ADDRESS, abi=abi)

fnames = []
for fname in sys.argv[1:]:
    if fname[-4:] != '.csv':
        print("skipping non-csv file " + fname)
    else:
        try:
            with open(fname) as f:
                reader = csv.reader(f)
                test_row = next(reader)
            fnames.append(fname)
        except Exception as e:
            print(f"can't open file {fname} - skipping (exception: {str(e)})")

start_time = time.time()
last_update = 0
numfiles = len(fnames)
for i, fname in enumerate(fnames):
    with open(fname) as f:
        runtime = timedelta(seconds = int(time.time() - start_time))
        reader = csv.reader(f)
        numrows = len([r for r in reader])
        print(f"{runtime} - file {i+1} of {numfiles}: {fname} ({numrows} rows)")
        f.seek(0)
        output = []
        for j, row in enumerate(reader):
            if len(row) < 4 or len(row[3]) != 66:
                # print(f"skipping invalid row {i}")
                continue
            if len(row) > 4:
                deadline = row[4]
            else:
                tx = w3.eth.get_transaction(row[3])
                try:
                    obj, params = contract.decode_function_input(tx.input)
                except Exception as e:
                    print(f"failed to decode transaction {j} ({row[3]}), skipping")
                    continue

                index = [
                    k['name'] for k in obj.abi['inputs'][0]['components']
                ].index('deadline')
                deadline = params['params'][index]

            output.append([row[0], row[1], row[2], row[3], deadline])

            if time.time() - last_update > 0.1:
                prog = f"row {j+1} of {numrows} ({100*(j+1)/numrows:.2f}%)"
                print(prog, end='\r')
                last_update = time.time()

    with open(fname, 'w') as f:
        writer = csv.writer(f)
        for row in output:
            writer.writerow(row)
