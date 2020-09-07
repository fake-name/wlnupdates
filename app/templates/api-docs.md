## API Documentation


##### For any problems/questions, please open an [issue](https://github.com/fake-name/wlnupdates/issues/) on github. 

------

WLNUpdates has a fairly simple API. It talks JSON, both for commands and the response.
There is only one endpoint, different operations are denoted by the contents of the
POSTed JSON. The endpoint path is `/api`.

The API basically exposes the underlying calls that are used for generating the HTML content. In fact, in most cases the primary codepaths are literally the same, with just the response rendering differing. 

All commands must post data of mimetype `application/json`. A exmple jquery call for this API is [here](https://github.com/fake-name/wlnupdates/blob/master/app/static/js/editable.js#L496-L502).

Note that all non-read-only calls for the the API currently have CSRF protection via [Flask-WTF](http://flask-wtf.readthedocs.org/en/latest/csrf.html). This is handled via a `$.ajaxSetup` `beforeSend` callback [here](https://github.com/fake-name/wlnupdates/blob/master/app/static/js/editable.js#L530-L536). This requirement will be relaxed in the future, as soon as I determine a good way to still maintain a decent level of protection in it's absence. Currently, the CSRF token is passed to the endpoints via a [meta tag](https://github.com/fake-name/wlnupdates/blob/master/app/static/js/editable.js#L528) on each  HTML page.

For most calls, if you call the relevant API method with invalid/incorrect parameters, the error message should tell you how to fix your API call.


## API Calls

#### Concepts:

The API call broadly uses the concept of a item "ID", which is a number to abstractly refer to many items - tags, releases, series, publishers, etc... All API calls that return information on any object must be referred to by their ID when using the API to query for them, rather then their human readable names.

Due to this fact, all the list lookup functions return both the human readable item name, and the corresponding item ID.

Note that IDs are not globally unique. There may be valid items in multiple categories with the same ID. As such, a unambiguous identifier is actually the combination of the category *and* the ID.


In most cases, the ID can be used to construct a corresponding URL without too much work. For series, Series-ids correlate to URLs as: `https://www.wlnupdates.com/series-id/<series-id>/<slug>`. The slug is optional, and can be ignored or left out entirely. `https://www.wlnupdates.com/series-id/<series-id>/` or `https://www.wlnupdates.com/series-id/<series-id>/garbage` will 302 redirect to the full URL. 

For most other topics, there isn't a slug, but the construction is the same:

 - `https://www.wlnupdates.com/author-id/<author-id>/`
 - `https://www.wlnupdates.com/genre-id/<genre-id>/`
 - `https://www.wlnupdates.com/artist-id/<artist-id>/`
 - `https://www.wlnupdates.com/tag-id/<tag-id>/`
 - `https://www.wlnupdates.com/group-id/<group-id>/`
 - `https://www.wlnupdates.com/publisher-id/<publisher-id>/`


#### Structure:

All API calls are, at minimum, composed of a base JSON object containing the key `mode`, with the value of `mode` determining which function the request maps to.

API call responses are a JSON object with at minimum 3 keys: `{ 'error'   : error, 'message' : message, 'reload'  : shouldReload} `. If the API call returns data, it will be the object for a fourth key, `data`

**Always present:**

 - `error` - Status boolean, indicating whether the API encountered an error. True indicates that there was an error, false indicates the call succeeded. Malformed API requests result in an error response.
 - `message` - String error message containing a human-readable description of the issue the API call encountered, if any. Not allowable API errors map to a proper description, most parameter validation errors result in a generic error message.

**Optional:**

 - `data` - Object containing the return data from the API call. The `data` member is almost always a object.
 - `reload` - Boolean flag indicating whether the API call results in changes that require a page-reload to properly display. Ignoreable (and in fact not present) for API-only interfacing.

Floats/strings passed to integer parameters will be cast to integers, errors on cast will result in an error, and the API call having no effect.



## Read-Only API Methods


### `get-series-id` 

Note: `get-series-data` is a synonym for `get-series-id`. I don't remember why I have two synonyms for the same internal call.

Post:

    {
    	'id': 3, 
    	'mode': 'get-series-id'
    }

`id` is the series-id for the series in question.

Response:

    {'data': 
    	{
    		'alternatenames': 
    		[
    			'Hamachi',
                             'やはり俺の青春ラブコメはまちがっている。',
                             'My Teen Romantic Comedy is Wrong as I Expected',
                             '我的青春恋爱物 语果然有问题（小说）',
                             'My Teen Romantic Comedy SNAFU',
							 <snip>
                             'Oregairu',
                             'Yahari Ore no Seishun Love Come wa '
                             'Machigatteiru.'
			],
          'authors': [{'author': 'WATARI Wataru', 'id': 3},
                      {'author': 'Wataru Watari', 'id': 52604}],
          'covers': [{'chapter': None,
                      'description': None,
                      'id': 3,
                      'srcfname': 'i203641.jpg',
                      'url': 'https://www.wlnupdates.com/cover-img/3',
                      'volume': None},
							 <snip>
                     {'chapter': None,
                      'description': 'Yahari Ore no Seishun Rom-Com wa '
                                     'Machigatteiru. 10.5',
                      'id': 2264,
                      'srcfname': '5548.jpeg',
                      'url': 'https://www.wlnupdates.com/cover-img/2264',
                      'volume': 10.0}],
          'demographic': 'Male',
          'description': '<p>Yahari Ore no Seishun Rabukome wa Machigatte Iru. '
                         'is a romantic comedy which revolves around '
                         'antisocial high school student, Hachiman Hikigaya, '
                         'who has no friends, no girlfriend, and a severely '
                         'distorted view on life. When he sees his classmates '
                         'talking excitedly about living their adolescent '
                         'lives, he mutters, "They\'re a bunch of liars." When '
                         'he is asked about his future dreams, he responds, '
                         '"Not working." In an attempt to fix Hachiman\'s '
                         'twisted personality, his teacher forces him to join '
                         "the volunteer 'service club', where the only other "
                         "member happens to be one of the school's most "
                         'beautiful and smartest girls, Yukino '
                         'Yukinoshita.</p>',
          'genres': [{'genre': 'comedy', 'id': 4},
                     {'genre': 'drama', 'id': 5},
                     {'genre': 'harem', 'id': 16991},
                     {'genre': 'psychological', 'id': 36752},
                     {'genre': 'romance', 'id': 6},
                     {'genre': 'school-life', 'id': 7},
                     {'genre': 'seinen', 'id': 8},
                     {'genre': 'slice-of-life', 'id': 13994}],
          'id': 3,
          'illustrators': [{'id': 3572, 'illustrators': 'Ponkan⑧'},
                           {'id': 3, 'illustrators': 'Ponkan 8'},
                           {'id': 3782, 'illustrators': 'Ponkan8'}],
          'latest': {'chp': 8.0, 'frg': 0.0, 'vol': 14.0},
          'latest_published': 'Sat, 08 Feb 2020 21:50:33 GMT',
          'latest_str': 'vol. 14.0, ch. 8.0',
          'license_en': True,
          'most_recent': 'Sat, 08 Feb 2020 21:50:33 GMT',
          'orig_lang': None,
          'orig_status': '14 Volumes + 3 Side-story Volumes (6.5,7.5,10.5) '
                         '(Completed)',
          'origin_loc': None,
          'progress': {'chp': 8.0, 'frg': 0.0, 'vol': 14.0},
          'pub_date': 'Sat, 01 Jan 2011 00:00:00 GMT',
          'publishers': [{'id': 5653, 'publisher': 'Gagaga Bunko'},
                         {'id': 779, 'publisher': 'Shogakukan'},
                         {'id': 780, 'publisher': 'Yen Press'}],
          'rating': {'avg': 7.77142857142857, 'num': 35, 'user': -1},
          'rating_count': 35,
          'region': 'unknown',
          'releases': [{'chapter': 8.0,
                        'fragment': None,
                        'postfix': '',
                        'published': 'Fri, 03 Jan 2020 07:00:27 GMT',
                        'series': {'id': 3,
                                   'name': 'Yahari Ore no Seishun Rabukome wa '
                                           'Machigatte Iru.'},
                        'srcurl': 'https://kyakka.wordpress.com/2020/01/03/oregairu-volume-14-chapter-8-happy-birthday-yukino/',
                        'tlgroup': {'id': 102, 'name': 'Kyakka'},
                        'volume': 14.0},
                       {'chapter': 7.0,
                        'fragment': None,
                        'postfix': '',
                        'published': 'Thu, 26 Dec 2019 01:11:40 GMT',
                        'series': {'id': 3,
                                   'name': 'Yahari Ore no Seishun Rabukome wa '
                                           'Machigatte Iru.'},
                        'srcurl': 'https://kyakka.wordpress.com/2019/12/25/oregairu-volume-14-chapter-7/',
                        'tlgroup': {'id': 102, 'name': 'Kyakka'},
                        'volume': 14.0},
							 <snip>
                       {'chapter': 1.0,
                        'fragment': None,
                        'postfix': '',
                        'published': 'Sun, 14 Sep 2014 03:15:03 GMT',
                        'series': {'id': 3,
                                   'name': 'Yahari Ore no Seishun Rabukome wa '
                                           'Machigatte Iru.'},
                        'srcurl': 'https://kyakka.wordpress.com/2014/09/14/yahari-4koma-chapter-1/',
                        'tlgroup': {'id': 102, 'name': 'Kyakka'},
                        'volume': None},
                       {'chapter': 1.0,
                        'fragment': None,
                        'postfix': 'Prologue 1',
                        'published': 'Tue, 21 Feb 2017 04:02:12 GMT',
                        'series': {'id': 3,
                                   'name': 'Yahari Ore no Seishun Rabukome wa '
                                           'Machigatte Iru.'},
                        'srcurl': 'https://kyakka.wordpress.com/2015/06/25/yahari-light-novel-volume-a-prologue-1/',
                        'tlgroup': {'id': 102, 'name': 'Kyakka'},
                        'volume': None}],
          'similar_series': [{'id': 44440,
                              'title': 'Youkoso Jitsuryoku Shijou Shugi no '
                                       'Kyoushitsu e'},
                             {'id': 581,
                              'title': 'Death March kara Hajimaru Isekai '
                                       'Kyusoukyoku'},
                             {'id': 45289, 'title': 'Yowa-chara Tomozaki-kun'},
                             {'id': 33188,
                              'title': 'Genjitsushugisha no Oukokukaizouki'},
                             {'id': 1471,
                              'title': 'Mahouka Koukou no Rettousei'},
                             {'id': 2085,
                              'title': 'Arifureta Shokugyou de Sekai Saikyou'}],
          'tags': [{'id': 3, 'tag': 'adapted-to-anime'},
                   {'id': 4, 'tag': 'adapted-to-manga'},
                   {'id': 990206, 'tag': 'androgynous-characters'},
                   {'id': 436136, 'tag': 'anti-social-lead'},
                   {'id': 2165069, 'tag': 'average-looking-lead'},
                   {'id': 383940, 'tag': 'beautiful-female-lead'},
                   {'id': 2496059, 'tag': 'calm-lead'},
                   {'id': 2495814, 'tag': 'character-growth'},
                   {'id': 436167, 'tag': 'clever-lead'},
                   {'id': 6, 'tag': 'club/s'},
                   {'id': 348397, 'tag': 'comedy'},
                   {'id': 2496058, 'tag': 'cunning-lead'},
                   {'id': 510471, 'tag': 'drama'},
                   {'id': 393033, 'tag': 'egotistical-male-lead'},
                   {'id': 8, 'tag': 'female-dominance'},
                   {'id': 2496056, 'tag': 'hard-working-protagonist/s'},
                   {'id': 9, 'tag': 'harem-subtext'},
                   {'id': 2495819, 'tag': 'late-romance'},
                   {'id': 436850, 'tag': 'loner-lead'},
                   {'id': 2495822, 'tag': 'love-interest-falls-in-love-first'},
                   {'id': 434533, 'tag': 'love-triangle/s'},
                   {'id': 434534, 'tag': 'male-lead'},
                   {'id': 680083, 'tag': 'modern-day'},
                   {'id': 2495821, 'tag': 'philosophical'},
                   {'id': 11, 'tag': 'popular-female-lead'},
                   {'id': 348401, 'tag': 'romance'},
                   {'id': 348400, 'tag': 'school-life'},
                   {'id': 348398, 'tag': 'slice-of-life'},
                   {'id': 2495826, 'tag': 'slow-romance'},
                   {'id': 12, 'tag': 'social-outcast/s'},
                   {'id': 13, 'tag': 'talented-female-lead'},
                   {'id': 680084, 'tag': 'tsundere'}],
          'title': 'Yahari Ore no Seishun Rabukome wa Machigatte Iru.',
          'tl_type': 'translated',
          'total_watches': 4,
          'type': 'Novel',
          'watch': False,
          'watchlists': False,
          'website': None},
     'error': False,
     'message': None}


 
#### `get-artist-data`/`get-artist-id`

Post:

    {
    	'id': 3, 
    	'mode': `get-artist-id`
    }

Response:

    {'data': {'name': 'Ponkan 8',
              'series': [{'id': 3,
                          'title': 'Yahari Ore no Seishun Rabukome wa Machigatte '
                                   'Iru.'}]},
     'error': False,
     'message': None}


#### `get-author-data`/`get-author-id`

Post:

    {
    	'id': 3, 
    	'mode': `get-author-id`
    }

Response:

    {'data': {'name': 'WATARI Wataru',
              'series': [{'id': 3,
                          'title': 'Yahari Ore no Seishun Rabukome wa Machigatte '
                                   'Iru.'}]},
     'error': False,
     'message': None}



#### `get-genre-data`/`get-genre-id`

Post:

    {
    	'id': 3, 
    	'mode': `get-genre-id`
    }

Response:

Note: This response is not paginated, and can be quite large as a result.

	{'data': {'genre': 'shounen',
	          'series': [{'id': 298, 'title': '1/2 Prince'},
	                     {'id': 1, 'title': "3-Z Class's Ginpachi-sensei"},
	                     {'id': 57522, 'title': '400 Years Old Virgin Demon King'},
	                     {'id': 33430, 'title': '7Th'},
	                     <snip>
	                     {'id': 268,
	                      'title': 'Yuusha ni Nare Nakatta Ore wa Shibushibu '
	                               'Shuushoku o Ketsui Shimashita'},
	                     {'id': 56692, 'title': 'Yuusha no Segare'},
	                     {'id': 670,
	                      'title': 'Yuusha Party ni Kawaii Ko ga Ita node, '
	                               'Kokuhaku Shitemita.'},
	                     {'id': 1631, 'title': 'Zero no Tsukaima'},
	                     {'id': 1098, 'title': 'Zhan Long'}]},
	 'error': False,
	 'message': None}



#### `get-group-data`/`get-group-id`

Post:

    {
    	'id': 3, 
    	'mode': `get-group-id`
    }

Response:
Note: Feed and releases are paginated using the same page number.

    {'data': {'active-series': {'110407': 'The Girl Who Sold Her Body, Who Might '
                                      'Be The Person Who Bought Her',
                            '112300': "4 JK's Life in Another World!",
                            '1135': 'Manowa Mamono Taosu Nouryoku Ubau Watashi '
                                    'Tsuyokunaru',
                            '116475': "Blunt Type Ogre Girl's Way to Live "
                                      'Streaming',
                            '1540': 'Kansutoppu!',
                            '2326': 'Garudina okoku kokoku-ki',
                            '2352': 'Yuusha Yori Saikyouna Kuro Kishi',
                            '2696': "Astarte's Knight",
                            '33497': 'Gob Tensei',
                            '33498': 'Harassing Thief Girl',
                            '43995': 'Me and My Beloved Cat (Girlfriend)',
                            '56687': 'Yuri Maid Cafe',
                            '59183': 'Being Recognized as an Evil God, I '
                                     'Changed My Job to Guardian Deity of the '
                                     'Beastmen Country',
                            '59901': 'From Junior (Kouhai) to Girlfriend',
                            '60139': 'Just Loving You',
                            '62454': 'The Lonely Monster and The Blind Girl',
                            '84966': 'Small Village Tridente',
                            '88828': 'Onna dakara, to Party wo Tsuihou Sareta '
                                     'no de Densetsu no Majo to Saikyou Tag wo '
                                     'Kumimashita'},
          'alternate-names': ['TheLazy9', 'The Lazy 9'],
          'feed-paginated': [{'contents': 'N/A',
                              'guid': 'http://9ethtranslations.wordpress.com/?p=5758',
                              'linkurl': 'https://9ethtranslations.wordpress.com/2020/05/31/ogregirl-ch8/',
                              'published': 'Sat, 30 May 2020 20:54:33 GMT',
                              'region': 'eastern',
                              'srcname': 'The Lazy 9',
                              'tags': ['Uncategorized'],
                              'title': 'Ogregirl ch8',
                              'updated': 'Sat, 30 May 2020 21:16:26 GMT'},
                              <snip>
                             {'contents': 'N/A',
                              'guid': 'http://9ethtranslations.wordpress.com/?p=5421',
                              'linkurl': 'https://9ethtranslations.wordpress.com/2019/05/18/tridente-48/',
                              'published': 'Sat, 18 May 2019 06:23:24 GMT',
                              'region': 'eastern',
                              'srcname': 'The Lazy 9',
                              'tags': ['Uncategorized'],
                              'title': 'Tridente 48',
                              'updated': 'Sat, 18 May 2019 06:45:21 GMT'}],
          'group': 'TheLazy9',
          'id': 3,
          'releases-paginated': [{'chapter': 8.0,
                                  'fragment': 0.0,
                                  'include': True,
                                  'postfix': '',
                                  'published': 'Sat, 30 May 2020 21:10:24 GMT',
                                  'srcurl': 'https://9ethtranslations.wordpress.com/2020/05/31/ogregirl-ch8/',
                                  'volume': None},
                                  <snip>
                                 {'chapter': 14.0,
                                  'fragment': 0.0,
                                  'include': True,
                                  'postfix': '',
                                  'published': 'Thu, 05 Dec 2019 07:52:46 GMT',
                                  'srcurl': 'https://9ethtranslations.wordpress.com/2016/01/12/gob-tensei-chapter-14/',
                                  'volume': None}],
          'site': None},
    'error': False,
    'message': None}


#### `get-publisher-data`/`get-publisher-id`

Post:

    {
    	'id': 3, 
    	'mode': `get-publisher-id`
    }

Response:

	{'data': {'name': 'ROK Media',
	          'series': [{'id': 1139, 'title': 'Ark'},
	                     {'id': 43318, 'title': 'Ark The Legend'},
	                     {'id': 58531, 'title': 'Haroon'},
	                     {'id': 85800, 'title': 'Isaac'},
	                     {'id': 108349, 'title': 'Namjang Secretary'},
	                     {'id': 2975, 'title': 'Red Storm'},
	                     {'id': 49321, 'title': 'Taming Master'},
	                     {'id': 1387, 'title': 'The Legendary Moonlight Sculptor'},
	                     {'id': 98840,
	                      'title': 'The Monster Duchess and Contract Princess'}],
	          'site': None},
	 'error': False,
	 'message': None}



#### `get-tag-data`/`get-tag-id`

Post:

    {
    	'id': 3, 
    	'mode': `get-tag-id`
    }

Response:
Note: This response is not paginated, and can be quite large as a result.

	{'data': {'series': [{'id': 63327, 'title': '2013'},
	                     {'id': 56910, 'title': '86'},
	                     {'id': 1042, 'title': 'Absolute Duo'},
	                     {'id': 191, 'title': 'Accel World'},
	                     {'id': 1530, 'title': 'Adachi to Shimamura'},
	                     {'id': 65219, 'title': 'Adorable Food Goddess'},
	                     {'id': 2147, 'title': 'Ai no Kusabi'},
	                     {'id': 58404, 'title': 'Akatsuki no Yona'},
	                     {'id': 554, 'title': 'Alderamin on the Sky'},
	                     {'id': 34910, 'title': 'All-Duties Mage'},
	                     {'id': 502, 'title': 'Allison'},
	                     {'id': 812, 'title': 'Amagi Brilliant Park'},
	                     {'id': 2019, 'title': 'Another'},
	                    
	                     <snip>
	                     {'id': 53829, 'title': 'The Sky Crawlers'},
	                     {'id': 50936,
	                      'title': 'The Super High Schoolers Affording to Live in '
	                               'Another World!'},
	                     {'id': 104249, 'title': 'The Sword Dynasty'},
	                     {'id': 110739, 'title': 'The Tatami Galaxy'},
	                     {'id': 318, 'title': 'The Third'},
	                     {'id': 41960, 'title': 'The Tiger and I'},
	                     {'id': 77823,
	                      'title': 'This Hero Is Invincible but Too Cautious'},
	                     {'id': 85665, 'title': 'Those Years I Opened a Zoo'},
	                     {'id': 109400, 'title': 'Tianbao Fuyao Lu'},
	                     {'id': 1018, 'title': 'Toaru Majutsu no Index'},
	                     {'id': 50793, 'title': 'Toaru Majutsu no Index SS'},
	                     {'id': 1150, 'title': 'Tokyo Ravens'},
	                     {'id': 339, 'title': 'Toradora!'},
	                     {'id': 607, 'title': 'Toshokan Sensou'},
	                     {'id': 1199, 'title': 'Tsuki no Sango'},
	                     {'id': 575, 'title': 'TsunPri - Aishite Ohime-sama'},
	                     {'id': 107134,
	                      'title': 'Tsurune: Kazemai Koukou Kyuudoubu'},
	                     {'id': 56807,
	                      'title': 'Tsuujou Kougeki ga Zentai Kougeki de Ni-kai '
	                               'Kougeki no Okaa-san wa Suki desu ka?'},
	                     {'id': 34217,
	                      'title': 'Uchi no Musume no Tame naraba, Ore wa '
	                               'Moshikashitara Maou mo Taoseru kamo Shirenai '
	                               '(WN)'},
	                     {'id': 110738, 'title': 'Uchouten Kazoku'},
	                     {'id': 108565,
	                      'title': 'Uchouten Kazoku: Nidaime no Kichou'},
	                     {'id': 2256, 'title': 'Vampire Hunter D (novel)'},
	                     {'id': 44559, 'title': 'Violet Evergarden'},
	                     {'id': 569, 'title': 'Washio Sumi wa Yuusha de Aru'},
	                     {'id': 58439,
	                      'title': 'While Killing Slimes for 300 Years, I Became '
	                               'the MAX Level Unknowingly'},
	                     {'id': 35887, 'title': 'Wu Dong Qian Kun'},
	                     {'id': 1826, 'title': 'Xingchenbian'},
	                     {'id': 3,
	                      'title': 'Yahari Ore no Seishun Rabukome wa Machigatte '
	                               'Iru.'},
	                     {'id': 91571, 'title': 'Yes, No, or Maybe Half?'},
	                     {'id': 1665, 'title': 'Yoku Wakaru Gendai Mahou'},
	                     {'id': 462, 'title': 'Youjo Senki'},
	                     {'id': 44440,
	                      'title': 'Youkoso Jitsuryoku Shijou Shugi no Kyoushitsu '
	                               'e'},
	                     {'id': 45289, 'title': 'Yowa-chara Tomozaki-kun'},
	                     {'id': 268,
	                      'title': 'Yuusha ni Nare Nakatta Ore wa Shibushibu '
	                               'Shuushoku o Ketsui Shimashita'},
	                     {'id': 1006, 'title': 'Zaregoto Series'},
	                     {'id': 1288, 'title': 'Zero kara Hajimeru Mahou no Sho'},
	                     {'id': 1631, 'title': 'Zero no Tsukaima'},
	                     {'id': 2044, 'title': 'Ze Tian Ji'},
	                     {'id': 66967, 'title': 'Zombie Brother'}],
	          'tag': 'adapted-to-anime'},
	 'error': False,
	 'message': None}


#### `get-search`
TBD


#### Searching:

WLNUpdates has two search modes:

 - Title search: Fuzzy search by series title, across all series alternate-names
 - Parametric search: filter series by a combination of chapter counts, tags,
   genre, and source type, and sort by various options (alphabetically, total
   released chapters, or last chapter release date)

While it'd be really nice to have these search options be unified, that's not currently
possible due to limitations in my SQL skills.

##### Title search:

> For the following example search request:
> `{'title': 'The Book Eating Magician', 'mode': 'search-title'}``
>
> WLNUpdates would return results like the following as the `data` contents:
>
>     {'cleaned_search': 'the book eating magician',
>      'results': [
>                  {'match': [(1.0, 'The Book Eating Magician'), (0.5, 'The Book Eating Wizard')], 'sid': 58781},
>                  {'match': [(0.538462, 'The Man-Eating Man')], 'sid': 52127},
>                  {'match': [(0.433333, 'The Lost Magician')], 'sid': 4331},
>                  {'match': [(0.384615, 'The King of Kings and Magician of Magicians')], 'sid': 59236},
>                  {'match': [(0.382353, 'The Aberrant Magician')], 'sid': 43107},
>                  {'match': [(0.382353, 'Moonlight & the Magician')], 'sid': 4541},
>                  {'match': [(0.371429, 'The Shattered Magician')], 'sid': 35482},
>                  {'match': [(0.363636, "The Magician's Diary")], 'sid': 32471},
>                  {'match': [(0.342857, 'Magic King of the End')], 'sid': 32189},
>                  {'match': [(0.342105, 'The Reckless Trap Magician')], 'sid': 57061},
>                  {'match': [(0.342105, 'The Magician of the Staircase'),
>                             (0.311111, 'The Cursed Girl and the Evil Magician')], 'sid': 58786},
>                  {'match': [(0.333333, 'Magic: The Gathering')], 'sid': 43120},
>                  {'match': [(0.325, 'The Magician Wants Normalcy'),
>                             (0.317073, 'The Magician Wants Normality')], 'sid': 35554},
>                  {'match': [(0.318182, 'Welcome to the Man-Eating Dungeon')], 'sid': 42047},
>                  {'match': [(0.3125, 'The Book of meme')], 'sid': 58871},
>                  {'match': [(0.302326, 'The Journey of a Lazy Magician')], 'sid': 59033},
>                  {'match': [(0.3, 'Omni-Magician')], 'sid': 35874}
>                ]
>     }
>
> These results illustrate several critical components of how wlnupdates thinks of series.
> Core to this is the concept of *alternate names*, e.g. the fact that a series can have
> multiple different names that correspond to the same actual series. This is generally
> the series title in both english and the original language, as well as variations
> in how a series title is translated. For OEL content, this is primarily driven
> by the fact that people on RoyalRoadL seem to like to rename their series
> on a regular basis, for no reason that can be determined.
>
> In any event, WLNUpdates has a list of name synonyms that is maintained for
> every series, and the titlesearch is performed on *this* data, rather then
> the normal series information.
>
> As such, it is possible to return *multiple* results for the *same series*.
>
> The results format is relatively simple:
> `{'match': [(1.0, 'The Book Eating Magician'), (0.5, 'The Book Eating Wizard')], 'sid': 58781},`
> The `sid` key is self explanitory, it contains the series-id for the series the
> match corresponds to. The contents of the `match` key is a list of all alternate-names
> from a series the search term matched to, in order of descending similarity. For the
> above example, we can see that `(1.0, 'The Book Eating Magician')` has a similarity
> value of `1.0` (e.g. exact match). Additionally, that same series's name has also been
> translated as `(0.5, 'The Book Eating Wizard')`, which matched the search term with
> a similarity of `0.5`
>
> Additionally, searching is done on what is internally termed a "cleaned name", which
> is functionally the passed search parameter after some normalization. Principally
> things like smart quotes, unprintable characters, some HTML equivalent entities,
> and various punctuation are stripped from the string prior to search. The
> cleaned version of the passed search parameter is returned in the `cleaned_search`
> return value.
>
> Note that the results of a search are non-paginated, and internally
> limited to a maximum of 50 results for all cases.
>

##### Parametric Search:

The parametric search lets you filter and sort series by a number of
different parameters.

There are two endpoints relevant to parametric searching:

 - `enumerate-tags` returns a list of the various tags relevant to a search.
   Internally, this is the same call used to generate the tags block on the
   advanced search HTML page.
 - `search-advanced` Returns the actual search results.


######  `enumerate-tags` / `enumerate-genres`

> This endpoint requires no parameters other then the endpoint name:
> `{'mode': 'enumerate-tags'}` or  `{'mode': 'enumerate-genres'}`
>
> Response data:
>
>      [
>           ['20th-century', 2],
>           ['21st-century', 7],
>           ['abandoned-child', 17],
>           ['abduction', 2],
>           ['ability-steal', 14],
>           ['abnormal', 2],
>           ['absent-parent/s', 29],
>           ['academy', 90],
>           ['acting', 17],
>           ['action', 6108],
>           ['actor/s', 14],
>           ['adapted-from-manga', 8],
>           ['adapted-to-anime', 227],
>           ['adapted-to-drama', 65],
>           ['adapted-to-drama-cd', 28],
>                            [ snip some results ]
>      ]
>
>  The response is a set of 2-tuples, where each tuple consists of a tag/genre,
>  and the number of occurances that tag/genre has in the WLNUpdates dataset. For
>  convenience, the advanced search page on WLNUpdates separates tags/genres into "common"
>  tags/genres (tags/genres with more then 25 occurances), and "rare" rags (tags/genres
>  with less then25 occurances). Tags that only occur once in the entire website dataset
>  are not included.
>
>  The lists are generated from a materialized view that is updated once per hour,
>  so if you add a tag/genre to a series, it may not be reflected in this API call for a
>  short period of time.


######  `search-advanced`

> The `search-advanced` endpoint has a number of optional parameters:
>
>  - `title-search-text`
>     String to search in titles for. Note that this is less-comprehensive then the
>     `search-title` interface when purely searching for title-text, as it hides
>     the complexity present in the alternate name system. As such, the title displayed
>     for search results may not seem to match the search string, because the matched
>     series has an alternate name that happens to match the search term.
>  - `tag-category`
>     Dictionary or object consisting of (tag-text : include-flag) key-value sets
>  - `genre-category`
>     Dictionary or object consisting of (genre-text : include-flag) key-value sets
>  - `chapter-limits`
>     2-tuple consisting of (minimum chapter, maximum chapter). Passing None or 0 for
>     the one of the limits disables that limit.
>  - `series-type`
>     Dictionary or object consisting of (series-text : include-flag) key-value sets
>     Valid series types are the literal strings: `Translated` or `Original English Language`
>  - `sort-mode`
>     Literal string: `update`, `chapter-count`, or anything else (or empty) for `name`
>
>  In this context, an `include-flag` is the literal string `included` or `excluded`,
>  to include or exclude the relevant tag or series-type.
>
>
> There is also the ability to specify additional items to be included in the returned
> data. This is intended for use in applications that want to use the search results
> for more complex views.
>
>   - `include-results`
>     This must be a list of strings. Allowable values are:
>         + `description` - Include the text description of the series
>         + `covers` - Include the list of cover URLs/descriptions.
>         + `tags` - Include the item tags for each item in the return.
>         + `genres` - Include the item genres for each item in the return.
>  
>  Search-advanced can also be accessed as permalinks via some slighly janky GET abuse:
>  `https://www.wlnupdates.com/search?json=<stringified-post-json>`. Yes, this is feeding json as get parameters, and is super gross but was very easy to implement.
>  There is currently no way to get json-based responses via GET. this facility is basically just for a few browser nicieties.
>  
> Example:
>
> {
>       'mode'   : 'search-advanced',
>       'series-type'  : {'Translated' : 'included'},
>       'tag-category' : {
>           'ability-steal' : 'included',
>           'virtual-reality' : 'excluded'
>           },
>       'sort-mode' : "update",
>       'chapter-limits' : [40, 0],
>   }
>
> Example response:
>
>     {
>       "data": [
>         {'sid' : 34471, 'title' : "I Was a Sword When I Reincarnated (LN)",                        'latest_published' : 1501705475.0, 'release_count' :  92},
>         {'sid' : 52804, 'title' : "Living in this World with Cut & Paste",                         'latest_published' : 1501328118.0, 'release_count' :  50},
>         {'sid' : 308,   'title' : "Ubau Mono Ubawareru Mono",                                      'latest_published' : 1499408780.0, 'release_count' : 155},
>         {'sid' : 543,   'title' : "Isekai Shihai no Skill Taker ~Zero kara Hajimeru Dorei Harem~", 'latest_published' : 1497778895.0, 'release_count' :  97},
>         {'sid' : 57093, 'title' : "Acquiring Talent in a Dungeon",                                 'latest_published' : 1495512031.0, 'release_count' :  60},
>         {'sid' : 34591, 'title' : "Riot Grasper",                                                  'latest_published' : 1490010700.0, 'release_count' :  62},
>         {'sid' : 44135, 'title' : "Tensei Shitara Kyuuketsuki-san Datta Ken",                      'latest_published' : 1487715955.0, 'release_count' : 110}
>       ],
>       "error": false,
>       "message": null
>     }
>
>  Each item in the data member is a dict with at minimum the following for members:
>   - `sid`              Series ID
>   - `title`            Series Name
>   - `latest_published` Last chapter posted (as a unix timestamp)
>   - `release_count`    Total release count for series.
>
> Specifying additional `include-flag` parameters will cause more members to be inserted
> into each dictionary.
>
> Some examples of additional return data:
>
>
> Request:  
> 
>      {'mode': 'search-advanced', 'sort-mode': 'update', 'chapter-limits': [40, 0], 'include-results': ['covers'], 'title-search-text': 'Fire Girl'}
>      
> Response:
>      
>      
>     {
>       "data": [
>         {
>           "covers": [
>             {
>               "chapter": null,
>               "description": "Fire Girl 1-A",
>               "url": "://www.wlnupdates.com/cover-img/813/",
>               "volume": null
>             }
>           ],
>           "id": 302,
>           "latest_published": 1512947747.947579,
>           "release_count": 57,
>           "title": "Fire Girl"
>         },
>         {
>           "covers": [],
>           "id": 57269,
>           "latest_published": 1495840265.0,
>           "release_count": 75,
>           "title": "Swamp Girl!"
>         }
>       ],
>       "error": false,
>       "message": null
>     }
>
> Request:  
> 
>     {'mode': 'search-advanced', 'sort-mode': 'update', 'chapter-limits': [40, 0], 'include-results': ['genres'], 'title-search-text': 'Fire Girl'}
>     
> Response:
>     
>     
>     {
>       "data": [
>         {
>           "genres": [
>             {
>               "genre": "action",
>               "id": 15204
>             },
>             {
>               "genre": "adventure",
>               "id": 15205
>             },
>             {
>               "genre": "romance",
>               "id": 15206
>             },
>             {
>               "genre": "supernatural",
>               "id": 15207
>             }
>           ],
>           "id": 302,
>           "latest_published": 1512947747.947579,
>           "release_count": 57,
>           "title": "Fire Girl"
>         },
>         {
>           "genres": [
>             {
>               "genre": "adventure",
>               "id": 6525
>             },
>             {
>               "genre": "comedy",
>               "id": 6526
>             },
>             {
>               "genre": "drama",
>               "id": 6527
>             },
>             {
>               "genre": "fantasy",
>               "id": 6528
>             },
>             {
>               "genre": "gender-bender",
>               "id": 6529
>             },
>             {
>               "genre": "romance",
>               "id": 6530
>             },
>             {
>               "genre": "shoujo",
>               "id": 6531
>             }
>           ],
>           "id": 57269,
>           "latest_published": 1495840265.0,
>           "release_count": 75,
>           "title": "Swamp Girl!"
>         }
>       ],
>       "error": false,
>       "message": null
>     }
>
> Request:
> 
>     {'mode': 'search-advanced', 'sort-mode': 'update', 'chapter-limits': [40, 0], 'include-results': ['description'], 'title-search-text': 'Fire Girl'}
>     
> Response:
> 
>     {
>       "data": [
>         {
>           "description": "<p>\n  I think you've lost if you fall in love.\n </p>\n <p>\n  \u2014Hinooka Homura. Seiran High School 1st year.\n </p>\n <p>\n  She likes to talk with friends. What she doesn't like are essays. By the way, she's the type that gets sleepy after thinking for ten seconds. Basically she had the air of someone who had failed her high school debut.\n </p>\n <p>\n  When Homura received the invitation \"Why don't you try becoming a mage?\", she joined the exploration club which had ties with the United Nations. The club activities consisted of conducting research on an unknown planet.\n </p>\n <p>\n  Along with the Kendo boy Touya Takumi, Misasagi Mayo-senpai who was efficient both in her studies and in martial arts, as well as the golem Ameno, Homura parties with her friends and heads to the other world of Nutella, a huge scale planet that is several times the size of Jupiter.\n </p>",
>           "id": 302,
>           "latest_published": 1512947747.947579,
>           "release_count": 57,
>           "title": "Fire Girl"
>         },
>         {
>           "description": "<p> A capable adventurer \u2014 becomes a young girl!? Chris is a fine adventurer in his own right, but thanks to his own carelessness, he's forced into a life-or-death gamble. He doesn't even have the time to think 'I survived!?', before he realizes that his body has become female. So begins the story of his \u2014 or rather, her \u2014 suffering. </p>",
>           "id": 57269,
>           "latest_published": 1495840265.0,
>           "release_count": 75,
>           "title": "Swamp Girl!"
>         }
>       ],
>       "error": false,
>       "message": null
>     }
>     
> For all queries that return additional parmeters (tags/genres), the associated 
> `id` for each item will also be returned. 
> 
> There is a slight confounding factor here, as the release count property is the
> number of *releases*, rather then the total number of actual chapters. For sources
> that cross post on multiple sites, this number can be considerably inflated, as
> the cross posts are all counted as releases as well.


### Non-Authenticated API Methods

> **Set user rating for series: `set-rating`**
>
> Required keys:
>
> - `mode` - Literal string "`set-rating`"
> - `item-id` - Series-id for the series to rate. Integer, strings or floats will be automatically cast.
> - `rating` - Rating of item. Integer, allowable range 0-10. Strings or floats will be cast to integers.
>
> Ratings are unique to each user. If a user is not logged in, the rating is tied to the originating IP address.


### Authenticated Only API Methods

#### Logging in: `do-login`

Post:

    {
      'mode'          : 'do-login',
      'username' : <your username>,
      'password' : <your password>,
      'remember_me' : True,   # Optional
    }

Response on successful login:

    {
      'data': None, 
      'error': False, 
      'message': 'Logged in successfully'
    }

Otherwise, `error` will be True, and the contents of `message` will detail what went wrong.

Once you are logged in, you will no longer be API rate limited.

NOTE: the `do-login` API endpoint has a independent rate-limiting system that allows one call every 3 seconds as a security precaution. If you are behind NAT and this is causing issues, please open an [issue](https://github.com/fake-name/wlnupdates/issues/) on github. The rate limiting here is rather speculative and may be possible to remove in the future.


#### `get-watches`

Get you watches. You must be logged in for this to work.

Post:

    {
      'mode'          : 'get-watches',
      'active-filter' : 'active',     # OPTIONAL
    }

The active-filter parameter can be one of `'active', 'maybe-stalled', 'stalled', 'all'`.
These filter the returned items on your watched list by activity state. 
If omitted, defaults to all.

Response:


    {'data': [{'Amusing': [[{'extra_metadata': {'is_yaoi': False, 'is_yuri': False},
                           'id': 66866,
                           'name': '10 Years after saying "Leave this to me and '
                                   'go", I Became a Legend.',
                           'rating': 5.0,
                           'rating_count': 4,
                           'tl_type': 'translated'},
                          {'agg': 79.0, 'chp': 79.0, 'frag': -1, 'vol': -1},
                          {'agg': 245.0,
                           'chp': 245.0,
                           'date': 1598255671.0,
                           'frag': 0.0,
                           'vol': -1},
                          None],
                         [{'extra_metadata': {'is_yaoi': False, 'is_yuri': False},
                           'id': 33442,
                           'name': 'A Wild Last Boss Appeared',
                           'rating': 7.16216216216216,
                           'rating_count': 37,
                           'tl_type': 'translated'},
                          {'agg': 47.0, 'chp': 47.0, 'frag': -1, 'vol': -1},
                          {'agg': 182.0,
                           'chp': 182.0,
                           'date': 1599327613.0,
                           'frag': 0.0,
                           'vol': -1},
                          None],
                         [{'extra_metadata': {'is_yaoi': False, 'is_yuri': False},
                           'id': 62698,
                           'name': 'Adorable Treasured Fox: Divine Doctor Mother '
                            'rating': 7.42857142857143,
                            'rating_count': 7,
                            'tl_type': 'translated'},
                           {'agg': 68.0, 'chp': 68.0, 'frag': -1, 'vol': -1},
                           {'agg': 139.0,
                            'chp': 139.0,
                            'date': 1599266413.0,
                            'frag': 0.0,
                            'vol': -1},
                           None]],
    <....snip....>
             'z - Complete': []},
            ['Amusing',
             'Great',
             'Inbox',
             'z - Complete'],
            'active'],
    'error': False,
    'message': None}

The returned data has some duplicates as it's the internal data-structure used to drive the watch-list webpage. 
The contents of `data` is a 3 item list: [`watch list dict`, `list names`, `active filter`]

 - `watch list dict` is a dict of {"watch list name" : list of items in watch list}
   - The items in the list are each a 4 item list:
      ```
      [
          Series info,
          current reading progress,
          available reading progress,
          name override (if any)
      ]
      ```
    The name override is part of a faility to allow useres to have a series in their watched list under any of it's available alternate names. This is useful for contexts where the a series has two well known names (often the romanized japanese name, and the translated name).
    Basically, if this item isn't `None`, it's probably better to use it instead of the actual series name from the series-info entry.
 - `list names` is a list of all watch lists the user has created. This is redundant with the keys in the `watch list dict` object.
 - `active-filter` is just the currently active filter as passed through the `active-filter` argument. If the passed `active-filter` is invalid, this will reflect the default value.

#### Paginated responses:

Many API calls return paginated responses. In the case of a paginated object, additional metadata is inserted into the `data` call return object, to make client-management of the pagination easier:

 - `has_next` - Boolean indicating if there is a "next" page.
 - `has_prev` - Boolean indicating if there is a "previous" page.
 - `next_num` - The number for the "next" page that must be passed as the `offet` value to get the item set that follows the current set. Invalid if `has_next` is false.
 - `prev_num` - The number for the "next" page that must be passed as the `offet` value to get the item set that preceeds the current set. Invalid if `has_prev` is false.
 - `pages` - The integer number of pages that the result set is paginated into.
 - `per_page` - The number of items being returned per-page. For informational purposes only, at the moment.
 - `total` - The total number of items the current API call has found.

Currently, all paginated objects return the actual items in the `items` member of the `data` object

> **Sequence view browsing**
>
> These API calls are used for viewing bulk contents of different categories.
> Each category type behaves very similarly.
>
> Modes:
>
> - `get-series`
> - `get-oel-series`
> - `get-translated-series`
> - `get-artists`
> - `get-authors`
> - `get-genres`
> - `get-groups`
> - `get-publishers`
> - `get-tags`
> - `get-feeds`
> 
> 
> Recent Releases views (these underpin the "Latest {Category} releases" sections on the site homepage):
> 
> - `get-releases` (Aggregate of both OEL and tranlsated releases, sorted by most recent)
> - `get-oel-releases`  (OEL releases, sorted by most recent)
> - `get-translated-releases` (OEL releases, sorted by most recent)
> 
> 
> Required keys:
>
> - `mode` - One of the literal strings from above.
>
> Optional keys:
>
> - `offset` - Page to retreive. If there are more then 50 items in the response,
>   it will be paginated in sets of 50. Defaults to 1 if unspecified. Values < 1 are invalid.
> - `prefix` - Starting character to limit the query results to. Allowable values are
>   one of the > chars in the set: `abcdefghijklmnopqrstuvwxyz0123456789`. If not
>   specified, defaults to returning all items. The prefix string also must be of length 1.
>   TODO: Handle unicode here?
>
> Return examples:
>
> > `get-tags`
> > `response['data']['items']` =
> >
> >     {
> >       "data": {
> >         "has_next": true,
> >         "has_prev": false,
> >         "items": [
> >           {
> >             "id": 427,
> >             "tag": "20th-century"
> >           },
> >           {
> >             "id": 679,
> >             "tag": "21st-century"
> >           },
> >                       [ snip some results ]
> >           {
> >             "id": 729,
> >             "tag": "angel/s"
> >           },
> >           {
> >             "id": 801,
> >             "tag": "angst"
> >           }
> >         ],
> >         "next_num": 2,
> >         "pages": 20,
> >         "per_page": 50,
> >         "prev_num": 0,
> >         "total": 992
> >       },
> >       "error": false,
> >       "message": null
> >     }
>
> The API call has succeeded (`error == false`), as such there was no error message (`message ==
> null`). Additionally, we have the pagination information (`"next_num": 2, "pages": 20,
> "per_page": 50, "prev_num": 0, "total": 992`). Lastly, we have a list of objects in the `items`
> member.
>
> Each item is actually a pair of values, the human-readable name for the item, and the
> corresponding ID. In order to look up items by the item (for example, to get series that
> have a tag), the relevant API call must be passed the ID, rather then the string.



> **Manage reading progress: `read-update`**

> Required keys:

>
> - `mode` - Literal string "`read-update`"
> - `item-id` - Series-id for the series to set the reading state for. Integer.
> - `vol`  - Integer, containing volume progress.
> - `chp`  - Integer, containing chapter progress.
> - `frag` - Integer, containing fragment/sub-chapter progress.
>
> Each update is complete, and completely overwrites the existing progress state.
> Things like incrementing existing values must be handled by the client.


> **Manage watch state for series: `set-watch`**

> Required keys:

>
> - `mode` - Literal string "`set-watch`"
> - `item-id` - Series-id for the series to modify the watch state for. Integer.
> - `list` - String name of list for item. If the list doesn't exist, it is created. To remove
> 		an item from a list, set the list to the special value: `-0-0-0-0-0-0-0-no-list-0-0-0-0-0-0-0-0-`.
>
> Lists only exist as long as there are items on them. If all items are removed from a list, it is automatically deleted.
>


> **Update series information: `series-update`**

> Required keys:
>
> - `mode` - Literal string "`series-update`"
> - `item-id` - Series-id for the series to update information for. Integer.


### Not documented yet


> **Update group/translator information: `group-update`**

> Required keys:

>
> - `mode` - Literal string "`group-update`"
> - `item-id` - Series-id for the group to update the information for. Integer.
>



> **Add cover for series: `cover-update`**

> Required keys:

>
> - `mode` - Literal string "`cover-update`"
> - `item-id` - Series-id for the series to add a cover too. Integer.
>
>
>



