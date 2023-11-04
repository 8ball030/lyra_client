const {ethers, Contract} = require("ethers");

const axios = require('axios');
const dotenv = require('dotenv');


function getUTCEpochSec() {
    return Math.floor(Date.now() / 1000);
}

dotenv.config();

// Environment variables, double check these in the docs constants section
const PRIVATE_KEY = process.env.OWNER_PRIVATE_KEY
const PROVIDER_URL = 'https://l2-prod-testnet-0eakp60405.t.conduit.xyz'
// # old addresses
// const USDC_ADDRESS = '0xe80F2a02398BBf1ab2C9cc52caD1978159c215BD'
// const DEPOSIT_MODULE_ADDRESS = '0xB430F3AE49f9d7a9B93fCCb558424972c385Cc38'
// const CASH_ADDRESS = '0xb8a082B53BdCBFB7c44C8Baf2F924096711EADcA'
// const ACTION_TYPEHASH = '0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17'
// const STANDARD_RISK_MANAGER_ADDRESS = '0x089fde8A32CD4Ef8D9F69DAed1B4CD5aC67d1ed7'
// const DOMAIN_SEPARATOR = '0xff2ba7c8d1c63329d3c2c6c9c19113440c004c51fe6413f65654962afaff00f3'
// NEW ADDRESSES

const USDC_ADDRESS = '0xe80F2a02398BBf1ab2C9cc52caD1978159c215BD'
const DEPOSIT_MODULE_ADDRESS = '0x43223Db33AdA0575D2E100829543f8B04A37a1ec'
const CASH_ADDRESS = '0x6caf294DaC985ff653d5aE75b4FF8E0A66025928'
const STANDARD_RISK_MANAGER_ADDRESS = '0x28bE681F7bEa6f465cbcA1D25A2125fe7533391C'
const ACTION_TYPEHASH = '0x4d7a9f27c403ff9c0f19bce61d76d82f9aa29f8d6d4b0c5474607d9770d1af17'
const DOMAIN_SEPARATOR = '0x9bcf4dc06df5d8bf23af818d5716491b995020f377d3b7b64c29ed14e3dd1105'
// Ethers setup
const PROVIDER = new ethers.JsonRpcProvider(PROVIDER_URL);
const wallet = new ethers.Wallet(PRIVATE_KEY, PROVIDER);
const encoder = ethers.AbiCoder.defaultAbiCoder();  

const depositAmount = "10000";
const subaccountId = 0; // 0 For a new account

async function approveUSDCForDeposit(wallet, amount) {
    const USDCcontract = new ethers.Contract(
      USDC_ADDRESS,
      ["function approve(address _spender, uint256 _value) public returns (bool success)"],
      wallet
    );
    const nonce = await wallet.provider?.getTransactionCount(wallet.address, "pending");
    await USDCcontract.approve(DEPOSIT_MODULE_ADDRESS, ethers.parseUnits(amount, 6), {  
        gasLimit: 1000000,
        nonce: nonce
    });
}

function encodeDepositData(amount){
    let encoded_data = encoder.encode( // same as "encoded_data" in public/create_subaccount_debug
      ['uint256', 'address', 'address'],
      [
        ethers.parseUnits(amount, 6),
        CASH_ADDRESS,
        STANDARD_RISK_MANAGER_ADDRESS
      ]
    );
    return ethers.keccak256(Buffer.from(encoded_data.slice(2), 'hex')) // same as "encoded_data_hashed" in public/create_subaccount_debug
}

function generateSignature(subaccountId, encodedData, expiry, nonce) {
    const action_hash = ethers.keccak256(  // same as "action_hash" in public/create_subaccount_debug
        encoder.encode(
            ['bytes32', 'uint256', 'uint256', 'address', 'bytes32', 'uint256', 'address', 'address'],
            [
                ACTION_TYPEHASH,
                subaccountId,
                nonce,
                DEPOSIT_MODULE_ADDRESS,
                encodedData,
                expiry,
                wallet.address,
                wallet.address
            ]
        )
    );

    const typed_data_hash = ethers.keccak256( // same as "typed_data_hash" in public/create_subaccount_debug
        Buffer.concat([
            Buffer.from("1901", "hex"),
            Buffer.from(DOMAIN_SEPARATOR.slice(2), "hex"),
            Buffer.from(action_hash.slice(2), "hex"),
        ])
    );

    return wallet.signingKey.sign(typed_data_hash).serialized 
}

async function signAuthenticationHeader() {
    const timestamp = Date.now().toString();
    const signature = await wallet.signMessage(timestamp);
    return {
        "X-LyraWallet": wallet.address,
        "X-LyraTimestamp": timestamp,
        "X-LyraSignature": signature
    };
}

async function createSubaccount() {
    // An action nonce is used to prevent replay attacks
		// LYRA nonce format: ${CURRENT UTC MS +/- 1 day}${RANDOM 3 DIGIT NUMBER}
    const nonce = Number(`${Date.now()}${Math.round(Math.random() * 999)}`);
    const expiry = getUTCEpochSec() + 300; // 5 min

    const encoded_data_hashed = encodeDepositData(depositAmount); // same as "encoded_data_hashed" in public/create_subaccount_debug
    const depositSignature = generateSignature(subaccountId, encoded_data_hashed, expiry, nonce);
    const authHeader = await signAuthenticationHeader();

    await approveUSDCForDeposit(wallet, depositAmount);

    try {
        const response = await axios.request({
            method: "POST",
            url: "https://api-demo.lyra.finance/private/create_subaccount",
            data: {
                margin_type: "SM",
                wallet: wallet.address,
                signer: wallet.address,
                nonce: nonce,
                amount: depositAmount,
                signature: depositSignature,
                signature_expiry_sec: expiry,
                asset_name: 'USDC',
            },
            headers: authHeader,
        });
    
        console.log(JSON.stringify(response.data, null, '\t'));
    } catch (error) {
        console.error("Error depositing to subaccount:", error);
    }
}

createSubaccount();

