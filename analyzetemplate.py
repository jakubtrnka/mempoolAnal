#/usr/bin/env python3
import sys
import json
import requests
import os.path
import matplotlib.pyplot as plt
import numpy as np

# Run with global variables username, password as used in RPC interface in bitcoin daemon

def rpc_call( f ):
    def method( *args ):
        (method, params ) = f( *args ) 
        hdr = { "content-type": "application/json" }
        payload = { "id": "0", "jsonrpc": "1.0", "method": method, "params": params }
        server="http://localhost:8332"
        
        auth = requests.auth.HTTPBasicAuth(username, password)
        r = requests.post(server, data=json.dumps(payload), headers=hdr, auth=auth )
        if r.status_code == 200:
            data = json.loads( r.text )
            if data["error"] == None:
                return data["result"]
            else:
                print ("Error: " + data["error"] )
                raise RuntimeError("Bitcoin daemon request failed")
        else:
            print ("Error: " + str(r.status_code) )
            raise RuntimeError(json.loads(r.text)["error"]["message"])
    return method

@rpc_call
def getblocktemplate():
    return ["getblocktemplate",[]]

@rpc_call
def getmempoolancestors( txid, verbose = True ):
    return ["getmempoolancestors", [txid, 1 if verbose else 0]]

@rpc_call
def getrawmempool( verbose=True ):
    return ["getrawmempool", [True if verbose else False]]

@rpc_call
def getrawtransaction( txid ):
    return [ "getrawtransaction", [txid, 1] ]

def main(testmode = True):
    #bitcoin daemon RPC credentials
    global username, password
    if ( sys.argv.__len__() == 3 ):
        username, password = (sys.argv[1], sys.argv[2])
    else:
        bitcoinconf = os.path.expanduser("~/.bitcoin/bitcoin.conf")
        if ( not os.path.exists( bitcoinconf ) ):
                print("config file not found")
                return 1
        #assuming rpcuser=<user>\n and rpcpassword=<passwd>\n lines in config files
        with open(bitcoinconf, "r") as configfile:
            for line in configfile:
                if "rpcuser" in line:
                    username = line[8:-1]
                if "rpcpassword" in line:
                    password = line[12:-1]

    
    if testmode:
        with open("testData.json","r") as tstmp:
            testData = json.load( tstmp )
            mempool = dict()
            for i in testData:
                mempool[i] = testData[i]["mempool"]
    else:
        mempool = getrawmempool()


    txsize = np.ndarray(0)
    txoutsum = np.ndarray(0)
    txfeerate = np.ndarray(0)

    for i in mempool:
        if testmode:
            txouts = testData[i]["txouts"]
        else:
            try:
                txouts = getrawtransaction( i )["vout"]
            except RuntimeError:
                continue

        tmptxoutsum = 0
        for j in txouts:
            tmptxoutsum += j["value"]
        txoutsum = np.append(txoutsum, tmptxoutsum)
        txsize = np.append(txsize, mempool[i]["size"])
        txfeerate  = np.append(txfeerate, mempool[i]["fee"]/txsize[-1]*10**8)
    

    fig = plt.figure(figsize=(60,30))
    ax = plt.gca()
    ax.scatter(txsize, txfeerate, s=15)
    ax.set_xlabel("size [B]", {"size":18})
    ax.set_ylabel("fee [Sat/B]", {"size":18})
    ax.set_xscale('log')
    ax.set_yscale('log')

    plt.savefig("mempoolDump.png", c=txoutsum, bbox_inches='tight')
    
if __name__=="__main__":
    main(testmode = True)
