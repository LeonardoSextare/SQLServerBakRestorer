PERMISSOES_DE_RESTAURACAO = """
SELECT IS_SRVROLEMEMBER('sysadmin') AS sysadmin,
       IS_SRVROLEMEMBER('dbcreator') AS dbcreator,
       HAS_PERMS_BY_NAME(NULL, NULL, 'CREATE ANY DATABASE') AS cria_banco
"""
