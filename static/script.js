$(document).ready(function(){

	$noip_hidden=true;
	var movingtext="";

	$(".ipgroup .noip:gt(0)").hide();
	$(document).on('click',".ipgroup .linkb",function()
	{
		window.open($(this).attr("href"));
		return false
	});
	$("#showall").click(function()
	{
		if ($noip_hidden)
		{
			$(".ipgroup .noip:gt(0)").show();
			$noip_hidden=false;
		}
		else
		{
			$(".ipgroup .noip:gt(0)").hide();
			$noip_hidden=true;
		}
		return false
	});
	$(".ipgroup .link").click(function()
	{
		window.location=$(this).attr("href");
		return false;
	});


	$(document).on('click',".ipgroup .edit", function()
	{
		var obj = $(this);
		$.ajax({
			url: 'ajax/' + $(this).attr("href"),
			dataType: "json",
			success: function(json)
			{

				if (json.result=="0")
				{
					obj.parent().parent().hide();
					obj.parent().parent().html("<form action=\"" + "\" method=\"POST\" class=\"navbar-form\"><input name=\"comment\" class=\"noevent\" type=\"text\" value=\"" + json.comment + "\"><input name=\"ip\" type=\"text\" class=\"noevent\" value=\"" + json.ip + "\"><input name=\"port\" type=\"text\" class=\"noevent\" value=\"" + json.port + "\" style=\"width:40px;\"><input name=\"submit\" class=\"editbutton btn\" id=\"" + json.id + "\" type=\"submit\" value=\"Изменить\"></form>").fadeIn("slow");
				}
				else alert(json.result);
			}
		});
		return false;
	});

	$(document).on('click',".ipgroup .move", function()
	{
		var obj = $(this);
		$.ajax({
			url: 'ajax/' + $(this).attr("href"),
			dataType: "html",
			success: function(json)
			{
				obj.parent().parent().hide("fast");
				obj.parent().parent().after(json).next().hide().fadeIn("slow");
				$(".chzn-select").chosen({search_contains: true});

			}
		});
		return false;
	});

	$(document).on('click',".freeipedit", function()
	{
		var obj = $(this);
		$.ajax({
			url: '/ajax' + $(this).attr("href"),
			dataType: "json",
			success: function(json)
			{

				if (json.result=="0")
				{
					obj.parent().prev().hide();
					obj.parent().prev().html("<form action=\"" + "\" method=\"POST\" class=\"navbar-form\"><input name=\"comment\" class=\"noevent\" type=\"text\" value=\"" + json.comment + "\"><input name=\"submit\" class=\"freeipeditbutton btn\" id=\"" + json.ipaddr + "\" type=\"submit\" value=\"Изменить\"></form>").fadeIn("slow");
				}
				else alert(json.result);
			}
		});
		return false;
	});

	$(document).on('click',"#showipcalc", function()
	{
		var obj = $("#ipcalc");
		$.ajax({
			url: '/ajax/ipcalc',
			dataType: "html",
			success: function(json)
			{
				obj.html(json).fadeIn("slow");
			}
		});
		return false;
	});

	$(document).on('click',"#closeipcalc", function()
	{
		$("#ipcalc").fadeOut("slow");
	});

	$(document).on('click',".ipgroup .add", function()
	{
		var id = $(this).attr("href").match(/([0-9]+)/)[1];
		$(this).parent().parent().parent().children("ul:eq(0)").append("<div class=\"ipgroup\"><div class=\"noip\"><form action=\"" + "\" method=\"POST\" class=\"navbar-form\"><input name=\"comment\" class=\"noevent\" type=\"text\" value=\"\"><input name=\"submit\" class=\"addbutton btn\" id=\"" + id + "\" type=\"submit\" value=\"Добавить\"></form></div></div>").get(1);
		return false;
	});

	$(document).on('click',".ipgroup .del",function()
	{
		if (confirm('Удалить этот узел из списка?'))
		{
			var obj = $(this);
			$.getJSON('ajax/' + $(this).attr("href"), {}, function(json)
			{
				if (json.result=="0")
				{
					obj.parent().parent().parent().slideToggle(500).queue(function(next){obj.parent().parent().parent().remove()});
				}
				else alert(json.result);
			});
		}
		return false;
	});

	$(document).on('click',".ipgroup .flag", function()
	{
		var obj = $(this);
		$.ajax({
			url: 'ajax/' + $(this).attr("href"),
			dataType: "json",
			success: function(json)
			{
				if (json.result=="0")
				{
					obj.remove();
				}
			}
		});
		return false;
	});


	$(document).on('click',".noevent",function()
	{
		return false;
		event.preventDefault();
	});

	$(document).on('click',".editbutton",function()
	{
		var obj = $(this);
		var dataString = $(this).parent().serialize();
		$.ajax({
			url: 'ajax/editnode/' + $(this).attr("id") + "/",
			type: "POST",
			dataType: "json",
			data: dataString,
			cache: false,
			success: function(json)
			{
				if (json.result=="0")
				{
					var port="";
					if (obj.prev().prev().attr("value")=="0.0.0.0" || obj.prev().prev().attr("value")=="") 
					{
						if (obj.prev().attr("value")!="100") port="<small>" + obj.prev().attr("value") + "</small> ";
						if (obj.parent().parent().hasClass("withip")) obj.parent().parent().removeClass("withip");
						obj.parent().parent().addClass("noip");
						obj.parent().parent().append( port + obj.prev().prev().prev().attr("value") + "<span class=\"adminbut\"><a class=\"add\" href=\"?act=addnode&id=" + obj.attr("id") + "\"><img src=\"images/add.png\"></a><a class=\"edit\" href=\"?act=editnode&id=" + obj.attr("id") + "\"><img src=\"images/edit.png\"></a><a class=\"move\" href=\"?act=movenode&id=" + obj.attr("id") + "\"><img src=\"images/move.png\"></a><a class=\"del\" href=\"?act=deletenode&id=" + obj.attr("id") + "\"><img src=\"images/delete.png\"></a></span>").hide().show("slow");
						obj.parent().remove();
					}
					else  
					{
						if (obj.prev().attr("value")!="0") port="<small>" + obj.prev().attr("value") + "</small> ";
						if (obj.parent().parent().hasClass("noip")) obj.parent().parent().removeClass("noip");
						obj.parent().parent().addClass("withip");
						obj.parent().parent().append("<span class=\"label label-important\">" + port + "<a class=\"linkb\" href=\"http://" + obj.prev().prev().attr("value") + "/\">" + obj.prev().prev().prev().attr("value") + "</a></span> (<span class=\"ipaddr\">" + obj.prev().prev().attr("value") + "</span>)" + "<span class=\"adminbut\"><a class=\"add\" href=\"addnode/" + obj.attr("id") + "/\"><img src=\"static/images/add.png\"></a> <a class=\"edit\" href=\"editnode/" + obj.attr("id") + "/\"><img src=\"static/images/edit.png\"></a> <a class=\"move\" href=\"movenode/" + obj.attr("id") + "/\"><img src=\"static/images/move.png\"></a> <a class=\"del\" href=\"deletenode/" + obj.attr("id") + "/\"><img src=\"static/images/delete.png\"></a> </span>").hide().show("slow");
						obj.parent().remove();
					}
				}
				else alert(json.result);
			}
		});
		return false;
		event.preventDefault();
	});

	$(document).on('click',".addbutton",function()
	{
		var obj = $(this);
		var dataString = $(this).parent().serialize();
		var url = window.location.href;
		var catid = url.match(/cat=([0-9]+)/);
		if (catid == null) catid="0";
		else catid=catid[1];
		$.ajax({
			url: 'ajax/addnode/' + $(this).attr("id") + '/',
			type: "POST",
			dataType: "json",
			data: dataString,
			cache: false,
			success: function(json)
			{
				if (json.result=="0")
				{
					if (json.ip=="0.0.0.0" || json.ip=="")
					{
						if (obj.parent().parent().hasClass("withip")) obj.parent().parent().parent().removeClass("withip");
						obj.parent().parent().parent().attr("id", json.id).append("<ul></ul>")
						obj.parent().parent().addClass("noip");
						obj.parent().parent().append( json.comment +"<span class=\"adminbut\"><a class=\"add\" href=\"addnode/" + json.id + "/\"><img src=\"static/images/add.png\"></a> <a class=\"edit\" href=\"editnode/" + json.id + "/\"><img src=\"static/images/edit.png\"></a> <a class=\"move\" href=\"movenode/" + json.id + "/\"><img src=\"static/images/move.png\"></a> <a class=\"del\" href=\"deletenode/" + json.id + "/\"><img src=\"static/images/delete.png\"></a></span>").hide().show("slow");
						if (obj.parent().attr("id")=="addtoroot")
						{
							$("#0.ipgroup ul:eq(0)").append("<div class=\"ipgroup\"><div id=\"new\"></div>");
							obj.parent().appendTo("#new");
							$("#new").removeAttr("id");
						}
						else
						{
							obj.parent().remove();
						}
					}
					else
					{
						if (obj.parent().parent().hasClass("noip")) obj.parent().parent().removeClass("noip");
						obj.parent().parent().addClass("withip");
						obj.parent().parent().parent().append("<span class=\"label label-important\"><a class=\"linkb\" href=\"http://" + json.ip + "/\">" + json.comment + "</a></span> (<span class=\"ipaddr\">" + json.ip + "</span>)" + "<span class=\"adminbut\"><a class=\"add\" href=\"addnode/" + json.id + "/\"><img src=\"static/images/add.png\"></a> <a class=\"edit\" href=\"editnode/" + json.id + "/\"><img src=\"static/images/edit.png\"></a> <a class=\"move\" href=\"movenode/" + json.id + "/\"><img src=\"static/images/move.png\"></a> <a class=\"del\" href=\"deletenode/" + json.id + "/\"><img src=\"static/images/delete.png\"></a> </span>").hide().show("slow");
						obj.parent().parent().parent().parent().attr("id",json.id);
						obj.parent().remove();
					}
				}
				else alert(json.result);
			}
		});
		return false;
		event.preventDefault();
	});

	$(document).on('click',".movebutton",function()
	{
		var obj = $(this);
		var dataString = $(this).parent().serialize();
		$.ajax({
			url: 'ajax/movenode/' + $(this).attr("id") + "/",
			type: "POST",
			dataType: "json",
			data: dataString,
			cache: false,
			success: function(json)
			{
				if (json.result=="0")
				{
					$("#"+json.id+".ipgroup form").remove();
					$("#"+json.id+".ipgroup div").show("slow");
					$("#"+json.id+".ipgroup").appendTo("#"+json.parent+".ipgroup ul:eq(0)");
				}
				else alert(json.result);
			}
		});
		return false;
		event.preventDefault();
	});

	$(document).on('click',".freeipeditbutton",function()
	{
		var obj = $(this);
		var dataString = $(this).parent().serialize();
		$.ajax({
			url: '/ajax/freeip/editcomment/' + $(this).attr("id") + "/",
			type: "POST",
			dataType: "json",
			data: dataString,
			cache: false,
			success: function(json)
			{
				if (json.result=="0")
				{
					obj.parent().parent().html(json.comment)
				}
			}
		});
		return false;
		event.preventDefault();
	});

	jQuery.expr[':'].contains = function(a, i, m) 
	{
		return jQuery(a).text().toUpperCase().indexOf(m[3].toUpperCase()) >= 0;
	};
	$(document).on('keyup',".srch",function()
	{
		$('.ipgroup').hide().delay(500);
		var foundin = $('.ipgroup:contains("'+$(this).attr("value")+'")').delay(500).show();
		return false;
	});
	$(document).on('keyup',".ipfreesrch",function()
	{
		$('.freeip').hide().delay(500);
		var foundin = $('.freeip:contains("'+$(this).attr("value")+'")').delay(500).show();
		return false;
	});
	$(document).on('keyup',".srch2",function()
	{
		var nameofswitch=""
		var obj = $(this);
		if ($(this).attr("value").length==17)
		{
			$.ajax({
				url: 'ajax/getswitchbymac/' + $(this).attr("value")+"/",
				dataType: "json",
				success: function(json)
				{
					if (json.result=="0")
					{
						nameofswitch=json.comment;
						$('.ipgroup').hide().delay(500);
						var foundin = $('.ipgroup:contains("'+nameofswitch.trim()+'")').delay(500).show();
						return false;
					}
				}
			});
		}
		else
		{
			$('.ipgroup').show().delay(500);
		}
	});

	var hidden=true;

	$(document).on('click',".ipgroup",function()
	{
		$(this).find(".noip").slideToggle(0);
		return false;
	});
	
});
