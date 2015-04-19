/*!
 * Editable.
 * Part of wlnupdates.com
 */

function edit(containerId){

	var container = $('#'+containerId).first();
	var contentDiv = container.find(".rowContents");
	var spans = contentDiv.find("span");
	if (spans.length == 0)
	{
		console.log("No items? Wat? Error!");
		return;
	}
	var spantype = spans.first().attr('class')
	if (spantype == "singleitem")
	{
		console.log("Singleitem span!")
	}
	else if (spantype == "multiitem")
	{
		console.log("Multi-item span!")
	}
	else
	{
		console.log("Unknown span type! Wat?")
		return;
	}

	var editLink = container.find("#editlink").first();
	editLink.attr('onclick', "saveEdits('" + containerId + "'); return false;");
	editLink.html('[save]');
	console.log(editLink);
	console.log(containerId);

}

function saveEdits(containerId)
{
	var container = $('#'+containerId).first();

	var editLink = container.find("#editlink").first();
	editLink.attr('onclick', "return false;");
	editLink.html('[saving]');

	var params = {
		"wat" : false,
		"testing" : true,
		"intval" : 42
	}

	$.ajax({
		url : "/api",
		success : saveCallback(containerId),
		data: JSON.stringify(params),
		method: "POST",
		dataType: 'json',
		contentType: "application/json;",
	});

}


function saveCallback(containerId)
{
	return function(result)
	{
		console.log("Save callback!")
		var container = $('#'+containerId).first();
		var editLink = container.find("#editlink").first()
		editLink.attr('onclick', "edit('" + containerId + "'); return false;")
		editLink.html('[edit]')

	}
}