var timeout_link;
jQuery.fn.centered_popup = function() {
	if(window.devicePixelRatio !== undefined) 
	{
		dpr = window.devicePixelRatio;
	} else 
	{
		dpr = 1;
	}
	if (this.attr("id") == "review") 
	{
		this.css('position', 'fixed');
		this.css('top', '50%');
		this.css('left', '50%');
		this.css('margin-top','-223px');
		this.css('margin-left','-151px');
	}
	else 
	{
		this.css('position', 'fixed');
		this.css('top', '50%');
		this.css('left','50%');
		this.css('margin-top','-111px');
		this.css('margin-left','-151px');
	}
}

function show_notice(text, type, timeout)
{
	obj = $("#notice");
	obj.slideUp(200);
	clearTimeout(timeout_link);
	function show_div()
	{
		obj.attr('class', "alert alert-dismissable alert-" + type);
		obj.centered_popup()
		obj.html(text);
		obj.slideDown(200);
	}
	function hide_div()
	{
		obj.slideUp(200);
	}
	timeout = typeof timeout !== 'undefined' ? timeout : 5000;
	type = typeof type !== 'undefined' ? type : "notice";

	show_div();
	timeout_link = setTimeout(hide_div, timeout);
}

function set_html(obj, html, timeout)
{
	timeout = typeof timeout !== 'undefined' ? timeout : 200;
	obj.hide(timeout, function()
	{
		obj.html(html);
		obj.show(timeout);
	});
}

function append_html(obj, html, timeout)
{
	timeout = typeof timeout !== 'undefined' ? timeout : 200;
	obj.hide(timeout, function()
	{
		obj.append(html);
		obj.show(timeout);
	});
}

function remove_object(obj, timeout)
{
	timeout = typeof timeout !== 'undefined' ? timeout : 200;
	obj.hide(timeout, function()
	{
		obj.remove();
	});
}

function for_printing() {
	document.write($(".ipgroup").filter(':visible').html())
}

$(document).ready(function(){

	$noip_hidden=true;
	var movingtext="";

	$(".ipgroup .noip:gt(0)").hide();
	$(document).on('click',".ipgroup .linkb",function()
	{
		window.open($(this).attr("href"));
		return false;
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
		return false;
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
			url: 'ajax' + $(this).attr("href"),
			dataType: "json",
			error: function() 
			{
				show_notice("Connection error", "danger");
			},
			success: function(json)
			{

				if (json.result=="0")
				{
					set_html(obj.parents(".node").first(), json.html);
				}
				else show_notice("Unknown error", "danger");
			}
		});
		return false;
	});

	$(document).on('click',".ipgroup .move", function()
	{
		var obj = $(this);
		$.ajax({
			url: 'ajax' + $(this).attr("href"),
			dataType: "html",
			error: function() 
			{
				show_notice("Connection error", "danger");
			},
			success: function(json)
			{
				obj.parents(".node").hide("fast");
				obj.parents(".node").after(json).next().hide().fadeIn("slow");
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
			error: function() 
			{
				show_notice("Connection error", "danger");
			},
			success: function(json)
			{

				if (json.result=="0")
				{
					obj.parent().prev().hide();
					obj.parent().prev().html("<form action=\"" + "\" method=\"POST\" class=\"navbar-form\"><input name=\"comment\" class=\"noevent\" type=\"text\" value=\"" + json.comment + "\"><input name=\"submit\" class=\"freeipeditbutton btn\" id=\"" + json.ipaddr + "\" type=\"submit\" value=\"{{ _('Save') }}\"></form>").fadeIn("slow");
				}
				else show_notice("Unknown error", "danger");
			}
		});
		return false;
	});

	$(document).on('click',".freeipapply", function()
	{
		var obj = $(this);
		$.ajax({
			url: '/ajax' + $(this).attr("href"),
			dataType: "json",
			error: function() 
			{
				show_notice("Connection error", "danger");
			},
			success: function(json)
			{

				if (json.result=="0")
				{
					obj.parent().parent().remove();
				}
				else show_notice("Unknown error", "danger");
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
			error: function() 
			{
				show_notice("Connection error", "danger");
			},
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
		html = "<div class=\"ipgroup\"><div class=\"node noip\"><form action=\"" + "\" method=\"POST\" class=\"navbar-form\"><input name=\"comment\" class=\"noevent\" type=\"text\" value=\"\"><input name=\"submit\" class=\"addbutton btn btn-primary\" id=\"" + id + "\" type=\"submit\" value=\"{{ _('Add') }}\"></form></div></div>";
		append_html($(this).parents(".ipgroup").first().children("ul:eq(0)"), html);
		return false;
	});

	$(document).on('click',".ipgroup .del",function()
	{
		if (confirm("{{ _('Are you sure, you want to delete this node?') }}"))
		{
			var obj = $(this);
			$.getJSON('ajax' + $(this).attr("href"), {}, function(json)
			{
				if (json.result=="0")
				{
					remove_object(obj.parents(".ipgroup").first());
//					obj.parents(".ipgroup").first().slideToggle(500).queue(function(next){obj.parents(".ipgroup").first().remove()});
				}
				else show_notice("Unknown error", "danger");
			});
		}
		return false;
	});

	$(document).on('click',".checkall,.ipgroup .check",function()
	{
		var obj = $(this);
		var parent;
		console.log(obj.context.className);

		if (obj.context.className == "checkall")
		{
			parent = $("#0");
		}
		else
		{
			parent = obj.parents(".ipgroup").first();
		}
		parent.fadeTo( 250, 0.25, function() {
			$.ajaxSetup({
  				"error":function() {   
    			show_notice("Connection error", "danger");
    			parent.fadeTo("slow", 1.0);
			}});
			$.getJSON('ajax' + obj.attr("href"), {}, function(json)
			{
				if (json.result=="0")
				{
					for(node in json.nodes)
					{
						var curr = false;
						if (parent.attr('id') == node)
						{
							curr = parent.find("span")[0];
						}
						else
						{
							curr = parent.find("#" + node + " span")[0];
						}
						if (curr)
						{
							if (json.nodes[node] == '1')
							{
								curr.className = 'normal-ip';
							}
							else
							{
								curr.className = 'label label-danger';
							}
						}
					}
				}
				else
				{
					show_notice("Unknown error", "danger");
				}
				parent.fadeTo("slow", 1.0);
			})
		});
		return false;
	});

	$(document).on('click',".ipgroup .flag", function()
	{
		var obj = $(this);
		$.ajax({
			url: 'ajax/' + $(this).attr("href"),
			dataType: "json",
			error: function() 
			{
				show_notice("Connection error", "danger");
			},
			success: function(json)
			{
				if (json.result=="0")
				{
					remove_object(obj.remove());
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
		var dataString = $(this).parents("form").first().serialize();
		$.ajax({
			url: 'ajax/editnode/' + $(this).attr("id") + "/",
			type: "POST",
			dataType: "json",
			data: dataString,
			cache: false,
			error: function() 
			{
				show_notice("Connection error", "danger");
			},
			success: function(json)
			{
				if (json.result=="0")
				{
					var port="";
					if (json.ip == "0.0.0.0") 
					{
						if (json.port != "0") port = "<small>" + json.port + "</small> ";
						if (obj.parents(".node").first().hasClass("withip")) obj.parents(".node").first().removeClass("withip");
						obj.parents(".node").first().addClass("noip");
						obj.parents(".node").first().append( port + json.comment + json.adminbut).hide().show("slow");
						obj.parents(".node").first().children().first().remove();
					}
					else  
					{						if (json.port != "0") port="<small>" + json.port + "</small> ";
						if (obj.parents(".node").first().hasClass("noip")) obj.parents(".node").first().removeClass("noip");
						obj.parents(".node").first().addClass("withip");
						obj.parents(".node").first().append("<span class=\"label label-danger\">" + port + "<a class=\"linkb\" href=\"http://" + json.ip + "/\">" + json.comment + "</a></span> (<span class=\"ipaddr\">" + json.ip + "</span>)" + json.adminbut).hide().show("slow");

						obj.parents(".node").first().children().first().remove();
					}
				}
				else show_notice("Unknown error", "danger");
			}
		});
		return false;
		event.preventDefault();
	});

	$(document).on('click',".addbutton",function()
	{
		var obj = $(this);
		var dataString = $(this).parents("form").first().serialize();
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
			error: function() 
			{
				show_notice("Connection error", "danger");
			},
			success: function(json)
			{
				if (json.result == "0")
				{
					if (json.ip == "0.0.0.0" || json.ip == "")
					{
						if (obj.parents(".node").first().hasClass("withip")) obj.parents(".node").first().removeClass("withip");
						obj.parents(".ipgroup").first().attr("id", json.id).append("<ul></ul>");
						obj.parents(".node").first().addClass("noip");
						obj.parents(".node").first().append( json.comment + json.adminbut).hide().show("slow");
						if (obj.parents("form").first().attr("id")=="addtoroot")
						{
							$("#0.ipgroup ul:eq(0)").append("<div class=\"ipgroup\"><div class=\"node\" id=\"new\"></div>");
							obj.parents("form").first().appendTo("#new");
							$("#new").removeAttr("id");
						}
						else
						{
							obj.parents("form").first().remove();
						}
					}
					else
					{
						if (obj.parents(".node").first().hasClass("noip")) obj.parents(".node").first().removeClass("noip");
						obj.parents(".node").first().addClass("withip");
						obj.parents(".ipgroup").first().append("<span class=\"label label-danger\"><a class=\"linkb\" href=\"http://" + json.ip + "/\">" + json.comment + "</a></span> (<span class=\"ipaddr\">" + json.ip + "</span>)" + json.adminbut).hide().show("slow");
						obj.parents(".ipgroup").first().attr("id",json.id);
						obj.parents("form").first().remove();
					}
				}
				else if (json.result == "1") 
				{
					show_notice("Can't set empty name", "danger");
				}
				else show_notice("Unknown error", "danger");
			}
		});
		return false;
		event.preventDefault();
	});

	$(document).on('click',".movebutton",function()
	{
		var obj = $(this);
		var dataString = $(this).parents("form").first().serialize();
		$.ajax({
			url: 'ajax/movenode/' + $(this).attr("id") + "/",
			type: "POST",
			dataType: "json",
			data: dataString,
			cache: false,
			error: function() 
			{
				show_notice("Connection error", "danger");
			},
			success: function(json)
			{
				if (json.result=="0")
				{
					$("#"+json.id+".ipgroup form").remove();
					$("#"+json.id+".ipgroup div").show("slow");
					$("#"+json.id+".ipgroup").appendTo("#"+json.parent+".ipgroup ul:eq(0)");
				}
				else show_notice("Unknown error", "danger");
			}
		});
		return false;
		event.preventDefault();
	});

	$(document).on('click',".freeipeditbutton",function()
	{
		var obj = $(this);
		var dataString = $(this).parents("form").first().serialize();
		$.ajax({
			url: '/ajax/freeip/editcomment/' + $(this).attr("id") + "/",
			type: "POST",
			dataType: "json",
			data: dataString,
			cache: false,
			error: function() 
			{
				show_notice("Connection error", "danger");
			},
			success: function(json)
			{
				if (json.result=="0")
				{
					if (json.exists == "1")
					{
						obj.parent().parent().parent().remove();
					}
					else
					{
						obj.parent().parent().html(json.comment);
					}
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
		$(this).attr("value").split("|").forEach(function (oritem) {
			$('.ipgroup:contains("' + oritem + '")').delay(500).show();
		});
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
		var nameofswitch="";
		var obj = $(this);
		if ($(this).attr("value").length==17)
		{
			$.ajax({
				url: 'ajax/getswitchbymac/' + $(this).attr("value")+"/",
				dataType: "json",
				error: function() 
				{
					show_notice("Connection error", "danger");
				},
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
		if ($(this).find("form").length) {
			return false;
		}
		$(this).find(".noip").slideToggle(200);
		return false;
	});
	
});
