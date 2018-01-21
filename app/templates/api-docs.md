## API Documentation

### Note: the API is unfinished, because the person asking for it apparently evaporated.

#### I'd be happy to finish both the API and the associated documentation as soon as someone indicate they'll actually *use* it. Feel free to show interest on the [issue](https://github.com/fake-name/wlnupdates/issues/3) on github.

------

WLNUpdates has a fairly simple API. It talks JSON, both for commands and the response.
There is only one endpoint, different operations are denoted by the contents of the
POSTed JSON. The endpoint path is `/api`.

All commands must post data of mimetype `application/json`. A exmple jquery call for this API is [here](https://github.com/fake-name/wlnupdates/blob/master/app/static/js/editable.js#L496-L502).

Note that all non-read-only calls for the the API currently have CSRF protection via [Flask-WTF](http://flask-wtf.readthedocs.org/en/latest/csrf.html). This is handled via a `$.ajaxSetup` `beforeSend` callback [here](https://github.com/fake-name/wlnupdates/blob/master/app/static/js/editable.js#L530-L536). This requirement will be relaxed in the future, as soon as I determine a good way to still maintain a decent level of protection in it's absence. Currently, the CSRF token is passed to the endpoints via a [meta tag](https://github.com/fake-name/wlnupdates/blob/master/app/static/js/editable.js#L528) on each  HTML page.




## API Calls

#### Concepts:

The API call broadly uses the concept of a item "ID", which is a number to abstractly refer to many items - tags, releases, series, publishers, etc... All API calls that return information on any object must be referred to by their ID when using the API to query for them, rather then their human readable names.

Due to this fact, all the list lookup functions return both the human readable item name, and the corresponding item ID.

Note that IDs are not globally unique. There may be valid items in multiple categories with the same ID. As such, a unambiguous identifier is actually the combination of the category *and* the ID.

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
> - `get-artists`
> - `get-authors`
> - `get-genres`
> - `get-groups`
> - `get-publishers`
> - `get-tags`
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

More:
>
>
  - `get-releases`
  - `get-series`
  - `get-translated-releases`
  - `get-translated-series`
  - `get-watches`
  - `get-search`
  - `get-feeds`
  - `get-artist-data`
  - `get-author-data`
  - `get-genre-data`
  - `get-group-data`
  - `get-publisher-data`
  - `get-series-data`
  - `get-tag-data`
>


