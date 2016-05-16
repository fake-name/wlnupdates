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
> - `offset` - Page to retreive. If there are more then 50 items in the response, it will be paginated in sets of 50. Defaults to 1 if unspecified. Values < 1 are invalid.
> - `prefix` - Starting character to limit the query results to. Allowable values are one of the chars in the set: `abcdefghijklmnopqrstuvwxyz0123456789`. If not specified, defaults to returning all items. The prefix string also must be of length 1.
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
> The API call has succeeded (`error == false`), as such there was no error message (`message == null`). Additionally, we have the pagination information (`"next_num": 2, "pages": 20, "per_page": 50, "prev_num": 0, "total": 992`). Lastly, we have a list of objects in the `items` member.
> 
> Each item is actually a pair of values, the human-readable name for the item, and the corresponding ID. In order to look up items by the item (for example, to get series that have a tag), the relevant API call must be passed the ID, rather then the string.



To Document:  
 - `get-releases`            
 - `get-series`              
 - `get-translated-releases` 
 - `get-translated-series`   
 - `get-watches`             
 - `get-search`              
 - `get-feeds`               
 - `get-cover-img`           
 - `get-artist-id`           
 - `get-author-id`           
 - `get-genre-id`            
 - `get-group-id`            
 - `get-publisher-id`        
 - `get-series-id`           
 - `get-tag-id`              


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


> **Manage watch state for series: `set-watch`**

> Required keys:

> 
> - `mode` - Literal string "`set-watch`"
> - `item-id` - Series-id for the series to modify the watch state for. Integer.
> 


> **Update series information: `manga-update`**

> Required keys:

> 
> - `mode` - Literal string "`manga-update`"
> - `item-id` - Series-id for the series to update information for. Integer.
> - `list` - String name of list for item. If the list doesn't exist, it is created. To remove
> 		an item from a list, set the list to the special value: `-0-0-0-0-0-0-0-no-list-0-0-0-0-0-0-0-0-`.
> 
> Lists only exist as long as there are items on them. If all items are removed from a list, it is automatically deleted.


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


