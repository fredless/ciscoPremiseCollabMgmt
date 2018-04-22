# ciscoPremiseCollabMgmt
Python modules to simplify use of provisioning SOAP API's for the Cisco on-premise collab product suite; AXL, SQL, RIS, CUPI, etc.  Hammer approach: to provide quick operation and simplistic consumption, some modules forego WSDL file consumption and build envelopes by hand.  May revisit this in the future see whether caching can be of help.

Arranging in packages and submodules by product and API:
```
└───cucm.py: Cisco Communications Manager classes:
│       axl: Administrative XML used for wide-ranging provisioning tasks
│       controlcenter: control services running on a node    
└───unity
|       TBD
└───imp
        TBD
```
