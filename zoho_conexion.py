import urllib3
import json

class ZohoApi():
    def __init__(self):
        pass

    @staticmethod
    def get_hv(id_card):
        zoho_solicitud = 'https://creator.zoho.com/publishapi/v2/hq5colombia/hq5/report/HOJA_DE_VIDA_Report?privatelink=TA0sfNwpGzfGRv0yTwVQgkn35KeyezDbaNKyk96mdHpO7DMTBgXDmQKXE59VRVPbrTEVR9ZHmVY0wzr9NeznTSdqgCnrSPQJ0wxF&criteria=NO_IDENTIFICACI_N=="'+id_card+'"'
        print(zoho_solicitud)
        response = urllib3.PoolManager().request('GET', zoho_solicitud)
        print(json.loads(response.data.decode('utf-8')))


if __name__ == '__main__':
    x = ZohoApi()
    x.get_hv("1018510059")
