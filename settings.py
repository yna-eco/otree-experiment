from os import environ


SESSION_CONFIGS = [
    dict(
        name="my_experiment2",
        display_name="Market Experiments 1-5",
        app_sequence=["my_experiment2"],
        num_demo_participants=5,
    ),
]

ROOMS = [
    dict(
        name='ticket_market',
        display_name='市場実験ルーム',
        # 参加者ラベルを使わないなら、下の行は消してOK
        # participant_label_file='ticket_market.txt',
        use_secure_urls=False,
    ),
]


# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'JPY'
POINTS_CUSTOM_NAME = '円'
USE_POINTS = True

ROOMS = []

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """


SECRET_KEY = '9124132597123'

INSTALLED_APPS = [
    'otree',
    'my_experiment2',
]
