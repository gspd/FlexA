#!/bin/bash
               
	USUARIO="gspd"
	PASS="gspd"

	MASCARA_REDE="192.168.1."
	HOST=(208 109 5)

	for ip in "${HOST[@]}"
		do
			echo -n "Iniciando FlexA-server em node 192.168.1.$ip"
      		sshpass -p $PASS ssh $USUARIO@$MASCARA_REDE$ip "cd git/FlexA/ && git checkout send_parts > /dev/null 2>	/dev/null;  ./init_server.py > /dev/null & " &&
        	echo -e "\t\tOK"
		done
	
