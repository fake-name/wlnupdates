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


######  `enumerate-tags` 

> This endpoint requires no parameters other then the endpoint name:
> `{'mode': 'enumerate-tags'}`
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
>  The response is a set of 2-tuples, where each tuple consists of a tag, 
>  and the number of occurances that tag has in the WLNUpdates dataset. For 
>  convenience, the advanced search page on WLNUpdates separates tags into "common"
>  tags (tags with more then 25 occurances), and "rare" rags (tags with less then
>  25 occurances). Tags that only occur once in the entire website dataset
>  are not included.
>  
>  The tag list is generated from a materialized view that is updated once per hour,
>  so if you add a tag to a series, it may not be reflected in this API call for a 
>  short period of time.


######  `search-advanced` 

> The `search-advanced` endpoint has a number of optional parameters:
> 
>  - `tag-category`
>     Dictionary or object consisting of (tag-text : include-flag) key-value sets
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
>         [34471, "I Was a Sword When I Reincarnated (LN)",                        1501705475.0,  92],
>         [52804, "Living in this World with Cut & Paste",                         1501328118.0,  50],
>         [308,   "Ubau Mono Ubawareru Mono",                                      1499408780.0, 155],
>         [543,   "Isekai Shihai no Skill Taker ~Zero kara Hajimeru Dorei Harem~", 1497778895.0,  97],
>         [57093, "Acquiring Talent in a Dungeon",                                 1495512031.0,  60],
>         [34591, "Riot Grasper",                                                  1490010700.0,  62],
>         [44135, "Tensei Shitara Kyuuketsuki-san Datta Ken",                      1487715955.0, 110]
>       ],
>       "error": false,
>       "message": null
>     }
>  
>  Each item in the data member is a 4-tuple consisting of:
>   - `sid`
>   - Series Name
>   - Last chapter posted (as a unix timestamp)
>   - Total release count for series.
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
  - `get-artist-id`           
  - `get-author-id`           
  - `get-genre-id`            
  - `get-group-id`            
  - `get-publisher-id`        
  - `get-series-id`           
  - `get-tag-id`              
> 


