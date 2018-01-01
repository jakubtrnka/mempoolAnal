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

def main():
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

    
    mempool = getrawmempool()
    #mempool = {'d6fd91b3dbf0c78008d7be7194282d3acfe8bcdca902b30fdceeb52488242983': {'size': 226, 'fee': 0.001, 'modifiedfee': 0.001, 'time': 1513808657, 'height': 500320, 'descendantcount': 9, 'descendantsize': 2028, 'descendantfees': 900000, 'ancestorcount': 4, 'ancestorsize': 901, 'ancestorfees': 400000, 'depends': ['9fdbe81506f56d06f337d150eccd345301a78d5d1f0fa77fe5ea342cbb22743d']}, '4715e6e7424b3ca9e94b293daac91dd7e7dbc257f3fa4484bf60005e712ed5ed': {'size': 191, 'fee': 0.00032869, 'modifiedfee': 0.00032869, 'time': 1513591623, 'height': 500143, 'descendantcount': 1, 'descendantsize': 191, 'descendantfees': 32869, 'ancestorcount': 3, 'ancestorsize': 790, 'ancestorfees': 92869, 'depends': ['be718db9094a7ab9a318c5e11f1ac4cf80d66b9e37b6ea8c3293efe9f665d082']}, '9de9ad03fcb8579267bee25a1f4fb5914b545cd1ced3966c5580788e24ef7342': {'size': 226, 'fee': 0.00033562, 'modifiedfee': 0.00033562, 'time': 1513697587, 'height': 500143, 'descendantcount': 9, 'descendantsize': 1992, 'descendantfees': 434339, 'ancestorcount': 8, 'ancestorsize': 2984, 'ancestorfees': 500260, 'depends': ['99a6cd48ffb1ce09b11c7e70b0ce33d37c5ec728922200d950f8fcacc65b44ea']}, 'd73f934cd3f221ff8c1aa2219628751e5ff99318a7c21488c3f55db53ddbce20': {'size': 226, 'fee': 0.00035708, 'modifiedfee': 0.00035708, 'time': 1513591523, 'height': 500143, 'descendantcount': 7, 'descendantsize': 1836, 'descendantfees': 649872, 'ancestorcount': 8, 'ancestorsize': 4718, 'ancestorfees': 247628, 'depends': ['9c9553697dbd1230b945ad436c93b9894d0b4ef915dc5be41b6d572b95efe11b']}, 'c02825d34cb0cde32d5041250423df4818e2c74e3c55dee9cf0e7be5c55e02c3': {'size': 225, 'fee': 0.0005, 'modifiedfee': 0.0005, 'time': 1513793323, 'height': 500298, 'descendantcount': 24, 'descendantsize': 5408, 'descendantfees': 1200000, 'ancestorcount': 2, 'ancestorsize': 450, 'ancestorfees': 100000, 'depends': ['0116af8dffd4870886c2260de868a0317b962a8cb84c4d4d4802433a63d9ba4c']}}

    txsize = np.ndarray(0)
    txoutsum = np.ndarray(0)
    txfeerate = np.ndarray(0)
    for i in mempool.keys():
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
        #print( "%.3f %5d %9.5f" % (txfeerate[-1], txsize[-1], txoutsum[-1]))
        #txfeerate = np.append(txfeerate, 
    

    fig = plt.figure(figsize=(60,30))
    ax = plt.gca()
    ax.scatter(txsize, txfeerate, s=15)
    ax.set_xlabel("size [B]", {"size":18})
    ax.set_ylabel("fee [Sat/B]", {"size":18})
    ax.set_xscale('log')
    ax.set_yscale('log')

    plt.savefig("mempoolDump.png", c=txoutsum, bbox_inches='tight')
    
if __name__=="__main__":
    main()
