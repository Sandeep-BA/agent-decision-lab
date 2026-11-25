#!/usr/bin/env sh
# Author: Sandeep Belgavi. Builds a synthetic root -> intermediate -> leaf chain with keytool,
# then probes a server that sends only the leaf and one that sends leaf + intermediate.
# Requires JDK 17+ (keytool and java on PATH). All keys are throwaway and written to ./work.
set -eu
cd "$(dirname "$0")"
PW=changeit-demo
rm -rf work && mkdir work && cd work
kt() { keytool -noprompt -storetype PKCS12 -storepass "$PW" -keypass "$PW" "$@"; }

kt -genkeypair -alias root -keyalg EC -groupname secp256r1 -dname "CN=Book Store Demo Root" -ext bc:c -validity 30 -keystore root.p12
kt -genkeypair -alias inter -keyalg EC -groupname secp256r1 -dname "CN=Book Store Demo Intermediate" -validity 30 -keystore inter.p12
kt -genkeypair -alias leaf -keyalg EC -groupname secp256r1 -dname "CN=localhost" -validity 30 -keystore server-leaf-only.p12

kt -exportcert -rfc -alias root -keystore root.p12 -file root.pem
kt -certreq -alias inter -keystore inter.p12 -file inter.csr
kt -gencert -alias root -keystore root.p12 -infile inter.csr -outfile inter.pem -rfc -ext bc:c=ca:true,pathlen:0 -ext ku:c=keyCertSign,cRLSign -validity 30
kt -importcert -alias root -keystore inter.p12 -file root.pem
kt -importcert -alias inter -keystore inter.p12 -file inter.pem

kt -certreq -alias leaf -keystore server-leaf-only.p12 -file leaf.csr
kt -gencert -alias inter -keystore inter.p12 -infile leaf.csr -outfile leaf.pem -rfc -ext san=dns:localhost -ext eku=serverAuth -validity 7
# keytool -gencert writes the issued certificate followed by the issuer's chain
# (leaf, intermediate). Keep the first PEM block alone for the misconfigured server.
awk '/BEGIN CERTIFICATE/{n++} n==1' leaf.pem > served-leaf-only.pem
cp leaf.pem served-full-chain.pem
test "$(grep -c 'BEGIN CERTIFICATE' served-leaf-only.pem)" = 1
test "$(grep -c 'BEGIN CERTIFICATE' served-full-chain.pem)" = 2
kt -importcert -alias root -keystore trust-root.p12 -file root.pem

# A second leaf for the same key whose AIA extension points at a local stand-in URL.
kt -gencert -alias inter -keystore inter.p12 -infile leaf.csr -outfile leaf-aia.pem -rfc -ext san=dns:localhost -ext eku=serverAuth -ext aia=caIssuers:uri:http://127.0.0.1:18765/inter.cer -validity 7
awk '/BEGIN CERTIFICATE/{n++} n==1' leaf-aia.pem > served-leaf-only-aia.pem
kt -exportcert -alias inter -keystore inter.p12 -file inter.der

cd ..
echo "case=leaf-only"; java ChainProbe.java work/server-leaf-only.p12 work/served-leaf-only.pem work/trust-root.p12 "$PW"
echo "case=full-chain"; java ChainProbe.java work/server-leaf-only.p12 work/served-full-chain.pem work/trust-root.p12 "$PW"
echo "case=leaf-only, no AIA extension, property on"; java -Dcom.sun.security.enableAIAcaIssuers=true ChainProbe.java work/server-leaf-only.p12 work/served-leaf-only.pem work/trust-root.p12 "$PW"
echo "case=leaf-only with AIA URL, property off"; java ChainProbe.java work/server-leaf-only.p12 work/served-leaf-only-aia.pem work/trust-root.p12 "$PW" 18765 work/inter.der
echo "case=leaf-only with AIA URL, property on"; java -Dcom.sun.security.enableAIAcaIssuers=true ChainProbe.java work/server-leaf-only.p12 work/served-leaf-only-aia.pem work/trust-root.p12 "$PW" 18765 work/inter.der
echo "case=leaf-only with AIA URL, property on, URL unreachable"; java -Dcom.sun.security.enableAIAcaIssuers=true ChainProbe.java work/server-leaf-only.p12 work/served-leaf-only-aia.pem work/trust-root.p12 "$PW"
