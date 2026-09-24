from core import ad_api
from core.i18n import T

SEP = "=" * 52


def run_generation(structure, p, host, log):
    try:
        log(SEP)
        log(T("log_fichier", path=p["fto"]))
        log(T("log_api", host=host))
        log(SEP)

        log(T("log_verif_port"))
        ad_api.check_port(host)
        log(T("log_api_ok"))

        if p["nouveau_projet"]:
            log(T("log_nouveau_projet", path=p["fto"]))
            ad_api.new_project(host, p["fto"])
            log(T("log_nouveau_projet_ok"))
        else:
            log(T("log_ouverture", path=p["fto"]))
            ad_api.open_project(host, p["fto"])
            log(T("log_ouverture_ok"))

        rows = structure.build(host, p, log)

        log(T("log_fermeture"))
        ad_api.close_project(host)
        log(T("log_fermeture_ok"))

        log(SEP)
        log(T("syn_succes"))
        log(SEP)
        width = max([26] + [len(str(label)) + 1 for label, _ in rows])
        for label, value in rows:
            log(f"  {label:<{width}}: {value}")
        log(SEP)
        return True
    except Exception as ex:
        log(T("log_erreur", ex=ex))
        ad_api.close_project(host)
        return False
