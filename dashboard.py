#!/usr/bin/env python

from bottle import route, run, template, static_file

import urllib2
import simplejson
import pprint 
import re
import locale
import sys, os.path
import ConfigParser

config_path = os.path.join(os.environ["HOME"], '.CryptoDashTicker')
config = ConfigParser.RawConfigParser()
config.read(config_path)

slideshow = None
if len(sys.argv) > 2:
	slideshow = sys.argv[2]
if sys.argv[1] == 'slideshow':
	slideshow = 1

@route('/<coins>')
def markets(coins):
	markets = coins
	req = urllib2.Request("https://api.mintpal.com/market/summary", None)
	opener = urllib2.build_opener()
	f = opener.open(req)
	json = f.read()
	market_data = {
		'MintPal': {},
		'SwissCEX': {}
	}
	mintpal = simplejson.loads(json)
	for m in mintpal:
		m['name'] = m['code']
		m['code'] = m['name'] + '/' + m['exchange']
		m['code'] = m['code'].upper()
		market_data['MintPal'][m['code']] = m
		
	req = urllib2.Request("http://api.swisscex.com/quotes?apiKey=%s" % (config.get('api', 'swisscex_key')), None)
	opener = urllib2.build_opener()
	f = opener.open(req)
	json = f.read()
	swisscex = simplejson.loads(json)
	for k in swisscex:
		keymap = {
			'volume24': '24hvol',
			'low24': '24hlow',
			'high24': '24hhigh',
			'lastPrice': 'last_price',
			'to': 'exchange',
			'from': 'name'
		};
		swisscex[k]['code'] = k
		for key in keymap:
			swisscex[k][keymap[key]] = swisscex[k][key]
		market_data['SwissCEX'][swisscex[k]['code']] = swisscex[k]
	coin_template = ''
	for coin in coins.split('_'):
		# Python dies id dict keys dont exist?
		# Anyway, crazy loop tp set them
		ltck = coin.upper()+'/LTC'
		btck = coin.upper()+'/BTC'
		swiss = market_data['SwissCEX']
		mint = market_data['MintPal']
		for ex in [swiss,mint]:
			for key1 in [ltck,btck]:
				if key1 not in ex:
					ex[key1] = {}
				for key2 in ['24hvol','24hhigh','24hlow','last_price','change']:
					if key2 not in ex[key1]:
						ex[key1][key2] = ''
					else:
						volc = ' LTC' if key1 == ltck else ' BTC'
						if key2 in ['24hvol','change']:
							ex[key1][key2] = '{0:.02f}'.format(float(ex[key1][key2]))
							ex[key1][key2] += volc if key2 == '24hvol' else ''
						else:
							ex[key1][key2] = int(float(ex[key1][key2]) * 100000000)
							ex[key1][key2] = "{:,}".format(ex[key1][key2])
							#ex[key1][key2] = '{0:.08f}'.format(ex[key1][key2])
		exchange = ''
		market = ''
		change = ''
		color = 'primary'
		if mint[btck]['change']:
			exchange = 'MintPal'
			market = 'BTC'
			change = mint[btck]['change']
		elif swiss[btck]['change']:
			exchange = 'SwissCEX'
			market = 'BTC'
			change = swiss[btck]['change']
		elif mint[ltck]['change']:
			exchange = 'MintPal'
			market = 'LTC'
			change = mint[ltck]['change']
		elif swiss[ltck]['change']:
			exchange = 'SwissCEX'
			market = 'LTC'
			change = swiss[ltck]['change']
		if change and float(change) > 0:
			color = 'success'
		elif change and float(change) < 0:
			color = 'danger'
		ltcmarket = ''
		btcmarket = ''
		avail = ''
		if mint[ltck]['change'] or swiss[ltck]['change']:
			ltcmarket = 1
		if  swiss[btck]['change'] or mint[btck]['change']:
			btcmarket = 1
		if ltcmarket  or btcmarket:
			avail = 1
		coin_template += template('''
{{!slidestart}}
<div class="panel panel-{{color}} {{avail}}">
	<div class="panel-heading">
		<div class="panel-title">
			{{coin_title}} {{change}} ({{exchange}} {{market}})
		</div>
	</div>
	<div class="panel-body">
		<div class="coinmarket {{avail}}">
			<div class="last">
				<div class="market {{btcmarket}}">
					<h3>BTC</h3>
					<span class="p s">{{swisscexbtc_last_price}}</span>
					<span class="p m">{{mintpalbtc_last_price}}</span>
				</div>
				<div class="market {{ltcmarket}}">
					<h3>LTC</h3>
					<span class="p s">{{swisscexltc_last_price}}</span>
					<span class="p m">{{mintpalltc_last_price}}</span>
				</div>
			</div>
			<div class="high">
				<div class="market {{btcmarket}}">
					<h3></h3>
					<span class="p s">{{swisscexbtc_24hhigh}}</span>
					<span class="p m">{{mintpalbtc_24hhigh}}</span>
				</div>
				<div class="market {{ltcmarket}}">
					<h3></h3>
					<span class="p s">{{swisscexltc_24hhigh}}</span>
					<span class="p m">{{mintpalltc_24hhigh}}</span>
				</div>
			</div>
			<div class="low">
				<div class="market {{btcmarket}}">
					<h3></h3>
					<span class="p s">{{swisscexbtc_24hlow}}</span>
					<span class="p m">{{mintpalbtc_24hlow}}</span>
				</div>
				<div class="market {{ltcmarket}}">
					<h3></h3>
					<span class="p s">{{swisscexltc_24hlow}}</span>
					<span class="p m">{{mintpalltc_24hlow}}</span>
				</div>
			</div>
			<div class="end vol">
				<div class="market {{btcmarket}}">
					<h3></h3>
					<span data-market="BTC" data-coin="{{coin_title}}" class="p s">{{swisscexbtc_24hvol}}</span>
					<span data-market="BTC" data-coin="{{coin_title}}" class="p m">{{mintpalbtc_24hvol}}</span>
				</div>
				<div class="market {{ltcmarket}}">
					<h3></h3>
					<span data-coin="{{coin_title}}" data-market="LTC" class="p s">{{swisscexltc_24hvol}}</span>
					<span data-coin="{{coin_title}}" data-market="LTC" class="p m">{{mintpalltc_24hvol}}</span>
				</div>
			</div>
			
		</div>
	</div>
</div>
{{!slideend}}
		''',
			avail= 'show' if avail else 'hide',
			ltcmarket= 'show' if ltcmarket else 'hide',
			btcmarket= 'show' if btcmarket else 'hide',
			change=change,
			exchange=exchange,
			market=market,
			color=color,
			coin_title=coin.upper(),
			swisscexbtc_24hvol=swiss[btck]['24hvol'],
			swisscexltc_24hvol=swiss[ltck]['24hvol'],
			mintpalbtc_24hvol=mint[btck]['24hvol'],
			mintpalltc_24hvol=mint[ltck]['24hvol'],
			swisscexbtc_24hhigh=swiss[btck]['24hhigh'],
			swisscexltc_24hhigh=swiss[ltck]['24hhigh'],
			mintpalbtc_24hhigh=mint[btck]['24hhigh'],
			mintpalltc_24hhigh=mint[ltck]['24hhigh'],
			swisscexbtc_24hlow=swiss[btck]['24hlow'],
			swisscexltc_24hlow=swiss[ltck]['24hlow'],
			mintpalbtc_24hlow=mint[btck]['24hlow'],
			mintpalltc_24hlow=mint[ltck]['24hlow'],
			swisscexbtc_last_price=swiss[btck]['last_price'],
			swisscexltc_last_price=swiss[ltck]['last_price'],
			mintpalbtc_last_price=mint[btck]['last_price'],
			mintpalltc_last_price=mint[ltck]['last_price'],
			slidestart='' if not slideshow else '''
			<div class="item">
			''',
			slideend='' if not slideshow else '''
			</div>
			'''
		)
	tick = sys.argv[1].upper() if sys.argv[1] != 'slideshow' else 'DOGE'
	tick_color = 'green' if float(market_data['MintPal'][tick+'/BTC']['change']) > 0 else 'red'
	invert = float(market_data['MintPal'][tick+'/BTC']['change'])
	invert = invert * -1 if invert < 0 else invert
	tick_change = '{0:.02f}'.format(float(invert))
	tick_last = market_data['MintPal'][tick+'/BTC']['last_price']
	return template('''
<!DOCTYPE html>
<html>
	<head>
		<title>{{doge}}</title>
		<meta http-equiv="refresh" content="300">
		<link rel="shortcut icon" type="image/png" href="favicon32.ico">
		<link rel="stylesheet" type="text/css" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css">
	    <script type="text/javascript" src="//code.jquery.com/jquery-2.1.0.min.js"></script>
		<script type="text/javascript" src="//netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js"></script>
		<style type="text/css">
		body{
			padding: 1em;
			font-family: Helvetica;
		}
		.panel-body{
			padding: 1em;
		}
		
		.panel.small{
			font-size: .8em;
		}
		.panel.small .panel-body, .panel.small .panel-heading {
			padding: .3em 1em;
		}
		.panel.small .panel-body h4 {
			font-size: 15px;
		}
		.coinmarket{
			height: 4em;
			width: 100%;
		}
		.vol,.low,.high,.last{
			float: left;
			width: 25%;
			position: relative;
		}
		.coinmarket h4 {
			font-size: 1.3em;
			margin: .3em 0;
			font-weight: bold;
		}
		.coinmarket h3 {
			font-size: 1.1em;
			margin: .3em 0;
			height: 20px;
			font-weight: bold;
		}
		.coinmarket h3:empty{
			height: 20px;
		}
		.coinmarket .end .s:after{
			content: "SwissCEX";
			padding-left: .3em;
			display: inline-block;
			font-weight: bold;
			color: rgb(122, 0, 255);
			position: absolute;
			cursor: pointer;
			right: 0;
		}
		.coinmarket .end .m:after{
			content: "MintPal";
			padding-left: .3em;
			display: inline-block;
			font-weight: bold;
			color: rgb(0, 153, 255);
			position: absolute;
			cursor: pointer;
			right: 0;
		}
		.carousel-control {
			opacity: 0;
		}
		.carousel-control:hover{
			opacity: .9;
		}
		.coinmarket .p{
			display: block;
		}
		.coinmarket .p:empty{
			display: none;
		}
		{{!largepanel}}
		</style>
		<script type="text/javascript">
		var markets = {{!markets}};
		$(function(){
			$('.s,.m').on('click',function(){
				var $this = $(this);
				var mint = /\\bm\\b/.test($this.attr('class'));
				var coin = $this.attr('data-coin'),
					market = $this.attr('data-market');
				var url = '//www.mintpal.com/market/'+coin+'/'+market;
				if (!mint){
					url = '//www.swisscex.com/market/'+coin+'_'+market;
				}
				window.open(url);
			});
			$('.carousel').find('.item').first().addClass('active')
		});
		/**
		 * @license MIT
		 * @fileOverview Favico animations
		 * @author Miroslav Magda, http://blog.ejci.net
		 * @version 0.3.4
		 */
		!function(){var e=function(e){"use strict";function t(e){if(e.paused||e.ended||w)return!1;try{d.clearRect(0,0,h,s),d.drawImage(e,0,0,h,s)}catch(o){}setTimeout(t,U.duration,e),L.setIcon(c)}function o(e){var t=/^#?([a-f\d])([a-f\d])([a-f\d])$/i;e=e.replace(t,function(e,t,o,n){return t+t+o+o+n+n});var o=/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(e);return o?{r:parseInt(o[1],16),g:parseInt(o[2],16),b:parseInt(o[3],16)}:!1}function n(e,t){var o,n={};for(o in e)n[o]=e[o];for(o in t)n[o]=t[o];return n}function r(){return document.hidden||document.msHidden||document.webkitHidden||document.mozHidden}e=e?e:{};var i,a,s,h,c,d,f,l,u,g,y,w,x,m={bgColor:"#d00",textColor:"#fff",fontFamily:"sans-serif",fontStyle:"bold",type:"circle",position:"down",animation:"slide",elementId:!1};x={},x.ff=/firefox/i.test(navigator.userAgent.toLowerCase()),x.chrome=/chrome/i.test(navigator.userAgent.toLowerCase()),x.opera=/opera/i.test(navigator.userAgent.toLowerCase()),x.ie=/msie/i.test(navigator.userAgent.toLowerCase())||/trident/i.test(navigator.userAgent.toLowerCase()),x.supported=x.chrome||x.ff||x.opera;var p=[];y=function(){},l=w=!1;var v=function(){i=n(m,e),i.bgColor=o(i.bgColor),i.textColor=o(i.textColor),i.position=i.position.toLowerCase(),i.animation=U.types[""+i.animation]?i.animation:m.animation;var t=i.position.indexOf("up")>-1,r=i.position.indexOf("left")>-1;if(t||r)for(var l=0;l<U.types[""+i.animation].length;l++){var u=U.types[""+i.animation][l];t&&(u.y=u.y<.6?u.y-.4:u.y-2*u.y+(1-u.w)),r&&(u.x=u.x<.6?u.x-.4:u.x-2*u.x+(1-u.h)),U.types[""+i.animation][l]=u}i.type=C[""+i.type]?i.type:m.type;try{a=L.getIcon(),c=document.createElement("canvas"),f=document.createElement("img"),a.hasAttribute("href")?(f.setAttribute("src",a.getAttribute("href")),f.onload=function(){s=f.height>0?f.height:32,h=f.width>0?f.width:32,c.height=s,c.width=h,d=c.getContext("2d"),b.ready()}):(f.setAttribute("src",""),s=32,h=32,f.height=s,f.width=h,c.height=s,c.width=h,d=c.getContext("2d"),b.ready())}catch(g){throw"Error initializing favico. Message: "+g.message}},b={};b.ready=function(){l=!0,b.reset(),y()},b.reset=function(){p=[],u=!1,d.clearRect(0,0,h,s),d.drawImage(f,0,0,h,s),L.setIcon(c)},b.start=function(){if(l&&!g){var e=function(){u=p[0],g=!1,p.length>0&&(p.shift(),b.start())};p.length>0&&(g=!0,u?U.run(u.options,function(){U.run(p[0].options,function(){e()},!1)},!0):U.run(p[0].options,function(){e()},!1))}};var C={},M=function(e){return e.n=Math.abs(e.n),e.x=h*e.x,e.y=s*e.y,e.w=h*e.w,e.h=s*e.h,e};C.circle=function(e){e=M(e);var t=!1;e.n>9&&e.n<100?(e.x=e.x-.4*e.w,e.w=1.4*e.w,t=!0):e.n>=100&&(e.x=e.x-.65*e.w,e.w=1.65*e.w,t=!0),d.clearRect(0,0,h,s),d.drawImage(f,0,0,h,s),d.beginPath(),d.font=i.fontStyle+" "+Math.floor(e.h*(e.n>99?.85:1))+"px "+i.fontFamily,d.textAlign="center",t?(d.moveTo(e.x+e.w/2,e.y),d.lineTo(e.x+e.w-e.h/2,e.y),d.quadraticCurveTo(e.x+e.w,e.y,e.x+e.w,e.y+e.h/2),d.lineTo(e.x+e.w,e.y+e.h-e.h/2),d.quadraticCurveTo(e.x+e.w,e.y+e.h,e.x+e.w-e.h/2,e.y+e.h),d.lineTo(e.x+e.h/2,e.y+e.h),d.quadraticCurveTo(e.x,e.y+e.h,e.x,e.y+e.h-e.h/2),d.lineTo(e.x,e.y+e.h/2),d.quadraticCurveTo(e.x,e.y,e.x+e.h/2,e.y)):d.arc(e.x+e.w/2,e.y+e.h/2,e.h/2,0,2*Math.PI),d.fillStyle="rgba("+i.bgColor.r+","+i.bgColor.g+","+i.bgColor.b+","+e.o+")",d.fill(),d.closePath(),d.beginPath(),d.stroke(),d.fillStyle="rgba("+i.textColor.r+","+i.textColor.g+","+i.textColor.b+","+e.o+")",e.n>999?d.fillText((e.n>9999?9:Math.floor(e.n/1e3))+"k+",Math.floor(e.x+e.w/2),Math.floor(e.y+e.h-.2*e.h)):d.fillText(e.n,Math.floor(e.x+e.w/2),Math.floor(e.y+e.h-.15*e.h)),d.closePath()},C.rectangle=function(e){e=M(e);var t=!1;e.n>9&&e.n<100?(e.x=e.x-.4*e.w,e.w=1.4*e.w,t=!0):e.n>=100&&(e.x=e.x-.65*e.w,e.w=1.65*e.w,t=!0),d.clearRect(0,0,h,s),d.drawImage(f,0,0,h,s),d.beginPath(),d.font="bold "+Math.floor(e.h*(e.n>99?.9:1))+"px sans-serif",d.textAlign="center",d.fillStyle="rgba("+i.bgColor.r+","+i.bgColor.g+","+i.bgColor.b+","+e.o+")",d.fillRect(e.x,e.y,e.w,e.h),d.fillStyle="rgba("+i.textColor.r+","+i.textColor.g+","+i.textColor.b+","+e.o+")",e.n>999?d.fillText((e.n>9999?9:Math.floor(e.n/1e3))+"k+",Math.floor(e.x+e.w/2),Math.floor(e.y+e.h-.2*e.h)):d.fillText(e.n,Math.floor(e.x+e.w/2),Math.floor(e.y+e.h-.15*e.h)),d.closePath()};var I=function(e,t){y=function(){try{if(e>0){if(U.types[""+t]&&(i.animation=t),p.push({type:"badge",options:{n:e}}),p.length>100)throw"Too many badges requests in queue.";b.start()}else b.reset()}catch(o){throw"Error setting badge. Message: "+o.message}},l&&y()},A=function(e){y=function(){try{var t=e.width,o=e.height,n=document.createElement("img"),r=o/s>t/h?t/h:o/s;n.setAttribute("src",e.getAttribute("src")),n.height=o/r,n.width=t/r,d.clearRect(0,0,h,s),d.drawImage(n,0,0,h,s),L.setIcon(c)}catch(i){throw"Error setting image. Message: "+i.message}},l&&y()},E=function(e){y=function(){try{if("stop"===e)return w=!0,b.reset(),w=!1,void 0;e.addEventListener("play",function(){t(this)},!1)}catch(o){throw"Error setting video. Message: "+o.message}},l&&y()},T=function(e){if(window.URL&&window.URL.createObjectURL||(window.URL=window.URL||{},window.URL.createObjectURL=function(e){return e}),x.supported){var o=!1;navigator.getUserMedia=navigator.getUserMedia||navigator.oGetUserMedia||navigator.msGetUserMedia||navigator.mozGetUserMedia||navigator.webkitGetUserMedia,y=function(){try{if("stop"===e)return w=!0,b.reset(),w=!1,void 0;o=document.createElement("video"),o.width=h,o.height=s,navigator.getUserMedia({video:!0,audio:!1},function(e){o.src=URL.createObjectURL(e),o.play(),t(o)},function(){})}catch(n){throw"Error setting webcam. Message: "+n.message}},l&&y()}},L={};L.getIcon=function(){var e=!1,t="",o=function(){for(var e=document.getElementsByTagName("head")[0].getElementsByTagName("link"),t=e.length,o=t-1;o>=0;o--)if(/icon/i.test(e[o].getAttribute("rel")))return e[o];return!1};if(i.elementId?(e=document.getElementById(i.elementId),e.setAttribute("href",e.getAttribute("src"))):(e=o(),e===!1&&(e=document.createElement("link"),e.setAttribute("rel","icon"),document.getElementsByTagName("head")[0].appendChild(e))),t=i.elementId?e.src:e.href,-1===t.indexOf(document.location.hostname))throw new Error("Error setting favicon. Favicon image is on different domain (Icon: "+t+", Domain: "+document.location.hostname+")");return e.setAttribute("type","image/png"),e},L.setIcon=function(e){var t=e.toDataURL("image/png");if(i.elementId)document.getElementById(i.elementId).setAttribute("src",t);else if(x.ff||x.opera){var o=a;a=document.createElement("link"),x.opera&&a.setAttribute("rel","icon"),a.setAttribute("rel","icon"),a.setAttribute("type","image/png"),document.getElementsByTagName("head")[0].appendChild(a),a.setAttribute("href",t),o.parentNode&&o.parentNode.removeChild(o)}else a.setAttribute("href",t)};var U={};return U.duration=40,U.types={},U.types.fade=[{x:.4,y:.4,w:.6,h:.6,o:0},{x:.4,y:.4,w:.6,h:.6,o:.1},{x:.4,y:.4,w:.6,h:.6,o:.2},{x:.4,y:.4,w:.6,h:.6,o:.3},{x:.4,y:.4,w:.6,h:.6,o:.4},{x:.4,y:.4,w:.6,h:.6,o:.5},{x:.4,y:.4,w:.6,h:.6,o:.6},{x:.4,y:.4,w:.6,h:.6,o:.7},{x:.4,y:.4,w:.6,h:.6,o:.8},{x:.4,y:.4,w:.6,h:.6,o:.9},{x:.4,y:.4,w:.6,h:.6,o:1}],U.types.none=[{x:.4,y:.4,w:.6,h:.6,o:1}],U.types.pop=[{x:1,y:1,w:0,h:0,o:1},{x:.9,y:.9,w:.1,h:.1,o:1},{x:.8,y:.8,w:.2,h:.2,o:1},{x:.7,y:.7,w:.3,h:.3,o:1},{x:.6,y:.6,w:.4,h:.4,o:1},{x:.5,y:.5,w:.5,h:.5,o:1},{x:.4,y:.4,w:.6,h:.6,o:1}],U.types.popFade=[{x:.75,y:.75,w:0,h:0,o:0},{x:.65,y:.65,w:.1,h:.1,o:.2},{x:.6,y:.6,w:.2,h:.2,o:.4},{x:.55,y:.55,w:.3,h:.3,o:.6},{x:.5,y:.5,w:.4,h:.4,o:.8},{x:.45,y:.45,w:.5,h:.5,o:.9},{x:.4,y:.4,w:.6,h:.6,o:1}],U.types.slide=[{x:.4,y:1,w:.6,h:.6,o:1},{x:.4,y:.9,w:.6,h:.6,o:1},{x:.4,y:.9,w:.6,h:.6,o:1},{x:.4,y:.8,w:.6,h:.6,o:1},{x:.4,y:.7,w:.6,h:.6,o:1},{x:.4,y:.6,w:.6,h:.6,o:1},{x:.4,y:.5,w:.6,h:.6,o:1},{x:.4,y:.4,w:.6,h:.6,o:1}],U.run=function(e,t,o,a){var s=U.types[r()?"none":i.animation];return a=o===!0?"undefined"!=typeof a?a:s.length-1:"undefined"!=typeof a?a:0,t=t?t:function(){},a<s.length&&a>=0?(C[i.type](n(e,s[a])),setTimeout(function(){o?a-=1:a+=1,U.run(e,t,o,a)},U.duration),L.setIcon(c),void 0):(t(),void 0)},v(),{badge:I,video:E,image:A,webcam:T,reset:b.reset}};"undefined"!=typeof define&&define.amd?define([],function(){return e}):"undefined"!=typeof module&&module.exports?module.exports=e:this.Favico=e}();
		$(function(){
			var favicon=new Favico({
			    bgColor : '{{bgcolor}}',
			    textColor : '#ff0',
			});
			favicon.badge({{change}});
		});
		</script>
	</head>
	<body>
	<div class="panel panel-default small">
		<div class="panel-heading">
			<div class="panel-title">
				Columns
			</div>
		</div>
		<div class="panel-body">
			<div class="last">
				<h4>Last Price</h4>
			</div>
			<div class="high">
				<h4>24H High</h4>
			</div>
			<div class="low">
				<h4>24H Low</h4>
			</div>
			<div class="vol">
				<h4>24H Volume</h4>
			</div>
		</div>
	</div>
	{{!slidestart}}
	{{!coins}}
	{{!slideend}}
	</body>
</html>
	''',
	markets=simplejson.dumps(market_data),
	coins=coin_template,
	doge=str(tick_change)+'% - '+str(tick_last)+'S - '+tick+'/BTC',
	change=tick_change,
	bgcolor=tick_color,
	slideend='' if not slideshow else '''
	   </div>
		<a class="left carousel-control" href="#carousel-example-generic" data-slide="prev">
	    <span class="glyphicon glyphicon-chevron-left"></span>
	  </a>
	  <a class="right carousel-control" href="#carousel-example-generic" data-slide="next">
	    <span class="glyphicon glyphicon-chevron-right"></span>
	  </a>

	</div>
	''',
	slidestart='' if not slideshow else '''
	<div id="carousel-example-generic" data-interval="10000" class="carousel slide" data-ride="carousel">
	  <ol class="carousel-indicators">
	    <li data-target="#carousel-example-generic" data-slide-to="0" class="active"></li>
	    <li data-target="#carousel-example-generic" data-slide-to="1"></li>
	    <li data-target="#carousel-example-generic" data-slide-to="2"></li>
	  </ol>
	  <div class="carousel-inner">
	''',
	largepanel='' if not slideshow else '''
	.panel { font-size: 3em} .panel-title { font-size: 1.3em} .coinmarket h3,.coinmarket h3:empty { margin: .3em 0; height: 50px; }
	'''
	)

run(host='localhost', port=3000)