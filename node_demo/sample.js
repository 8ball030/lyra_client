// This is a sample script that will submit an order to the Lyra testnet

// To run this script, you must have a Lyra testnet account with some ETH and LYRA in it


const { ethers } = require("ethers");
const { WebSocket } = require('ws');
const dotenv = require('dotenv');

dotenv.config();

const PRIVATE_KEY = process.env.OWNER_PRIVATE_KEY
const PROVIDER_URL = 'https://l2-prod-testnet-0eakp60405.t.conduit.xyz';
const WS_ADDRESS = process.env.WEBSOCKET_ADDRESS || 'ws://localhost:3000/ws';
const ACTION_TYPEHASH = '0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17';
const DOMAIN_SEPARATOR = '0xff2ba7c8d1c63329d3c2c6c9c19113440c004c51fe6413f65654962afaff00f3';
// const ASSET_ADDRESS = '0x8932cc48F7AD0c6c7974606cFD7bCeE2F543a124';
const ASSET_ADDRESS = '0x62CF2Cc6450Dc3FbD0662Bfd69af0a4D7485Fe4E';
const TRADE_MODULE_ADDRESS = '0x63Bc9D10f088eddc39A6c40Ff81E99516dfD5269';

const PROVIDER = new ethers.JsonRpcProvider(PROVIDER_URL);
const wallet = new ethers.Wallet(PRIVATE_KEY, PROVIDER);
const encoder = ethers.AbiCoder.defaultAbiCoder();
const subaccount_id = 550

const OPTION_NAME = 'ETH-PERP'
const OPTION_SUB_ID = '0' // can retreive with public/get_instrument


async function signAuthenticationHeader() {
  const timestamp = Date.now().toString();
  const signature = await wallet.signMessage(timestamp);  
    return {
      wallet: wallet.address,
      timestamp: timestamp,
      signature: signature,
    };
}

const connectWs = async () => {
    return new Promise((resolve, reject) => {
        const ws = new WebSocket(WS_ADDRESS);

        ws.on('open', () => {
            setTimeout(() => resolve(ws), 50);
        });

        ws.on('error', reject);

        ws.on('close', (code, reason) => {
            if (code && reason.toString()) {
                console.log(`WebSocket closed with code: ${code}`, `Reason: ${reason}`);
            }
        });
    });
};

async function loginClient(wsc ) {
    const login_request = JSON.stringify({
        method: 'public/login',
        params: await signAuthenticationHeader(),
        id: Math.floor(Math.random() * 10000)
    });
    wsc.send(login_request);
    console.log('Sent login request')
    console.log(login_request)
    await new Promise(resolve => setTimeout(resolve, 2000));
}

function defineOrder(){
    return {
        instrument_name: OPTION_NAME,
        subaccount_id: subaccount_id,
        direction: "buy",
        limit_price: 1310,
        amount: 100,
        signature_expiry_sec: Math.floor(Date.now() / 1000 + 300),
        max_fee: "0.01",
        nonce: Number(`${Date.now()}${Math.round(Math.random() * 999)}`), // LYRA nonce format: ${CURRENT UTC MS +/- 1 day}${RANDOM 3 DIGIT NUMBER}
        signer: wallet.address,
        order_type: "limit",
        mmp: false,
        signature: "filled_in_below"
    };
}

function encodeTradeData(order){
  let encoded_data = encoder.encode( // same as "encoded_data" in public/order_debug
    ['address', 'uint', 'int', 'int', 'uint', 'uint', 'bool'],
    [
      ASSET_ADDRESS, 
      OPTION_SUB_ID, 
      ethers.parseUnits(order.limit_price.toString(), 18), 
      ethers.parseUnits(order.amount.toString(), 18), 
      ethers.parseUnits(order.max_fee.toString(), 18), 
      order.subaccount_id, order.direction === 'buy']
    );
  return ethers.keccak256(Buffer.from(encoded_data.slice(2), 'hex')) // same as "encoded_data_hashed" in public/order_debug
}

async function signOrder(order) {
    const tradeModuleData = encodeTradeData(order)

    const action_hash = ethers.keccak256(
        encoder.encode(
          ['bytes32', 'uint256', 'uint256', 'address', 'bytes32', 'uint256', 'address', 'address'], 
          [
            ACTION_TYPEHASH, 
            order.subaccount_id, 
            order.nonce, 
            TRADE_MODULE_ADDRESS, 
            tradeModuleData, 
            order.signature_expiry_sec, 
            wallet.address, 
            order.signer
          ]
        )
    ); // same as "action_hash" in public/order_debug

    order.signature = wallet.signingKey.sign(
        ethers.keccak256(Buffer.concat([
          Buffer.from("1901", "hex"), 
          Buffer.from(DOMAIN_SEPARATOR.slice(2), "hex"), 
          Buffer.from(action_hash.slice(2), "hex")
        ]))  // same as "typed_data_hash" in public/order_debug
    ).serialized;
}

async function submitOrder(order, ws) {
    return new Promise((resolve, reject) => {
        const id = Math.floor(Math.random() * 1000);
        ws.send(JSON.stringify({
            method: 'private/order',
            params: order,
            id: id
        }));

        ws.on('message', (message) => {
            const msg = JSON.parse(message);
            if (msg.id === id) {
                console.log('Got order response:', msg);
                resolve(msg);
            }
        });
    });
}

async function completeOrder() {
    const ws = await connectWs();
    await loginClient(ws);
    const order = defineOrder();
    await signOrder(order);
    console.log('Submitting order:', order);
    await submitOrder(order, ws);
}

completeOrder();

