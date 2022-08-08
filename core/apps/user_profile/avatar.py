import random

AVATAR_URLS = {
    "MALE_AVATARS": [
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/male/iconAvatarIcMale1@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/male/iconAvatarIcMale2@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/male/iconAvatarIcMale3@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/male/iconAvatarIcMale4@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/male/iconAvatarIcMale5@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/male/iconAvatarIcMale6@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/male/iconAvatarIcMale7@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/male/iconAvatarIcMale8@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/male/iconAvatarIcMale9@3x.png",
    ],
    "FEMALE_AVATARS": [
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/female/iconAvatarIcFemale1@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/female/iconAvatarIcFemale2@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/female/iconAvatarIcFemale3@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/female/iconAvatarIcFemale4@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/female/iconAvatarIcFemale5@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/female/iconAvatarIcFemale6@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/female/iconAvatarIcFemale7@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/female/iconAvatarIcFemale8@3x.png",
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/female/iconAvatarIcFemale9@3x.png",
    ],
    "OTHER_AVATAR": [
        "https://pillar-public-bucket.s3.eu-west-2.amazonaws.com/avatar/other/iconAvatarIcOther@3x.png"
    ],
}


def get_avatar():
    return random.choice(AVATAR_URLS["OTHER_AVATAR"])
