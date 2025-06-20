from hmdb_lib import Metabolite



if __name__ == '__main__':
    from pprint import pprint
    metabolite = Metabolite.FromDB("db/hmdb.db", "HMDB0000002")
    pprint(metabolite)