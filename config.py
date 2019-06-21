class DevelopmentConfig:
    DEBUG = True

    DATABASE_URI = 'sqlite:///dev_database.db'
    TOKEN = "794766889:AAFvOD3zOdXi-OIYCN0cEq2fm06iZFm13jo"
    LINK_TO_BOT = 'https://t.me/devrobbot?start=%s'


class ProductionConfig:
    DEBUG = False

    DATABASE_URI = 'postgres+psycopg2://cwyzqcibwgfibp' \
                   ':35c8357e58aae1f7f11a8c7d9683f4043c44524f83309af717293fda96292462' \
                   '@ec2-54-221-214-3.compute-1.amazonaws.com:5432/dccefmk7lklpi1'
    TOKEN = "844180371:AAGzN2Ls-3tuseaN9h_R22l6FAL8ZqPav2I"

    LINK_TO_BOT = 'https://t.me/RobobetsBot?start=%s'
