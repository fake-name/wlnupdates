/*!
 * Editable.
 * Part of wlnupdates.com
 */

function singleEditable(spans, contentDiv, containerId)
{
	var content = spans.first().text()
	if (content == 'N/A') content = ""
	var contentArr = [
		"<textarea name='input-" + containerId + "' rows='2' id='singleitem'>"+content.trim()+"\n</textarea>",
		"<script>$('textarea').autogrow({onInitialize:true});</script>"
	]
	contentDiv.html(contentArr.join("\n"))
}

function multiEditable(spans, contentDiv, containerId)
{
	var content = ""
	spans.each(function(){
		content += $(this).find("a").first().text() + "\n"
	})
	// console.log(content)
	if (content == 'N/A') content = ""
	var contentArr = [
		"<p>One entry per line, please.</p>",
		"<textarea name='input-" + containerId + "' rows='2' id='multiitem'>"+content+"</textarea>",
		"<script>$('textarea').autogrow({onInitialize:true});</script>"
	]
	contentDiv.html(contentArr.join("\n"))
}



function edit(containerId){

	var container = $('#'+containerId).first();
	var contentDiv = container.find(".rowContents");
	var spans = contentDiv.find("span");
	if (spans.length == 0)
	{
		console.log("No items? Wat? Error!");
		return;
	}
	var spantype = container.attr('class')

	if (spantype.indexOf("singleitem") >= 0)
	{
		singleEditable(spans, contentDiv, containerId);
	}
	else if (spantype.indexOf("multiitem") >= 0)
	{
		multiEditable(spans, contentDiv, containerId);
	}
	else
	{
		console.log("Unknown span type: '"+spantype+"'! Wat?")
		return;
	}

	var editLink = container.find("#editlink").first();
	editLink.attr('onclick', "saveEdits('" + containerId + "'); return false;");
	editLink.html('[save]');
	// console.log(editLink);
	// console.log(containerId);

}

function saveEdits(containerId)
{
	var container = $('#'+containerId).first();

	var editLink = container.find("#editlink").first();
	editLink.attr('onclick', "return false;");
	editLink.html('[saving]');


	var entryType = container.find("textarea").attr('id');
	var entryArea = container.find("textarea").first().val();
	var mangaId = $('meta[name=manga-id]').attr('content')

	var params = {
		"mode"      : "manga-update",
		"mangaId"   : mangaId,
		"type"      : entryType,
		"contents"  : entryArea,
		"c-type"    : containerId,
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
		if (!result.hasOwnProperty("error"))
		{
			console.log("No error result?")
		}
		if (result['error'])
		{
			alert("Error on update!\n\nMessage from server:\n"+result["message"])
		}
		else
		{
			location.reload();
		}
		console.log(result)

		// var container = $('#'+containerId).first();
		// var editLink = container.find("#editlink").first()
		// editLink.attr('onclick', "edit('" + containerId + "'); return false;")
		// editLink.html('[edit]')


		// var container = $('#'+containerId).first();
		// var contentDiv = container.find(".rowContents");

		// var spantype = container.attr('class')

		// if (spantype.indexOf("singleitem") >= 0)
		// {
		// 	singleStatic(spans, contentDiv, containerId);
		// }
		// else if (spantype.indexOf("multiitem") >= 0)
		// {
		// 	console.log("Multi-item span!")
		// }
		// else
		// {
		// 	console.log("Unknown span type! Wat?")
		// 	return;
		// }


	}
}

var csrftoken = $('meta[name=csrf-token]').attr('content')

$.ajaxSetup({
	beforeSend: function(xhr, settings) {
		if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
			xhr.setRequestHeader("X-CSRFToken", csrftoken)
		}
	}
})