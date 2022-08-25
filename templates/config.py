
from templates import ImportDataFromInflux
token = "CjNhQHje2pEPhEkv3YrZQPAVnRtGm4sfBIN7KDJuYZderM3NIqStIzWprARxcc5XgiMv_WbWSwKzGti_hlxfsw=="
org = "cadis_framatome"



def get_bucket_list() :
    L=ImportDataFromInflux.get_bucket_list(ImportDataFromInflux.url,token,org)
    return(L)

L=get_bucket_list()
pages = ['Home'] + L

dicobucket={}
for el in L :
    dicobucket[el]= el.lower()[:-1]