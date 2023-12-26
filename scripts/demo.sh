#! /bin/bash

set -e

SLEEP_TIME=3

cowsay The lyra V2 client offers both a library and a cli tool to manage positions on LyraV2.

sleep $SLEEP_TIME

clear

cowsay "The client can be installed from pip as so;" 

echo "pip install lyra-v2-client"

sleep $SLEEP_TIME

clear

cowsay "Once the lyra client is installed, we can programatically interact with lyra"

lyra

sleep $SLEEP_TIME
clear

cowsay we can fetch markets by instrument type and currency

lyra instruments fetch --help

sleep $SLEEP_TIME
clear

echo \`lyra instruments fetch -i perp\`
lyra instruments fetch -i perp

sleep $SLEEP_TIME
clear

echo \`lyra instruments fetch -i perp -c btc\`
lyra instruments fetch -i perp -c btc
sleep $SLEEP_TIME
clear



cowsay we can manage orders
echo \`lyra orders\`
lyra orders
sleep $SLEEP_TIME
clear

cowsay we can create orders
echo \`lyra orders create -s sell -i ETH-PERP -a 1 -p 3000\`
lyra orders create -s sell -i ETH-PERP -a 1 -p 3000
sleep $SLEEP_TIME
clear

cowsay "we can then retrieve them"
echo \`lyra orders fetch -i ETH-PERP --status open\`
lyra orders fetch -i ETH-PERP --status open
sleep $SLEEP_TIME
clear


cowsay "we can then cancel them"
echo \`lyra orders cancel_all\`
lyra orders cancel_all
sleep $SLEEP_TIME
clear

cowsay "we can also check our balances"
echo \`lyra collateral fetch\`
lyra collateral fetch
sleep $SLEEP_TIME
clear

cowsay "we can also check our positions"
echo \`lyra positions fetch\`
lyra positions fetch
sleep $SLEEP_TIME
clear

