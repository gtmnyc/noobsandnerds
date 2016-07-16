# -*- coding: utf-8 -*-
#
#      Copyright (C) 2014 Sean Poyser and Richard Dean (write2dixie@gmail.com) - With acknowledgement to some original code by twinther (Tommy Winther)

import xbmc
import xbmcaddon
import xbmcgui
import os
import dixie
import download
import extract

ADDON           = xbmcaddon.Addon(id = 'script.tvportal')
HOME            = ADDON.getAddonInfo('path')
ICON            = os.path.join(HOME, 'icon.png')
ICON            = xbmc.translatePath(ICON)
ADDONS          = xbmc.translatePath('special://home/addons')
PACKAGES        = os.path.join(ADDONS, 'packages')
SF_CHANNELS     =  ADDON.getSetting('SF_CHANNELS')
dialog          = xbmcgui.Dialog()
dp              = xbmcgui.DialogProgress()

#---------------------------------------------------------------------------------------------------
def CheckIdle(maxIdle):
    if maxIdle == 0:
        return
    
    idle = xbmc.getGlobalIdleTime()
    if idle < maxIdle:
        return

    delay = 60
    count = delay
    dp.create("TV Portal","Streaming will automatically quit in %d seconds" % count, "Press Cancel to contine viewing")
    dp.update(0)
              
    while xbmc.Player().isPlaying() and count > 0 and not dp.iscanceled():
        xbmc.sleep(1000)
        count -= 1
        perc = int(((delay - count) / float(delay)) * 100)
        if count > 1:
            dp.update(perc,"Streaming will automatically quit in %d seconds" % count, "Press Cancel to contine viewing")
        else:
            dp.update(perc,"Streaming will automatically quit in %d second" % count, "Press Cancel to contine viewing")            

    if not dp.iscanceled():
        xbmc.Player().stop()
#---------------------------------------------------------------------------------------------------
def get_params(p):
    param=[]
    paramstring=p
    if len(paramstring)>=2:
        params=p
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
           params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param
#---------------------------------------------------------------------------------------------------
def playSF(url):
    dixie.log("### URL: "+url)
    launchID = '10025'
    if xbmcgui.Window(10000).getProperty('OTT_LAUNCH_ID') == launchID:
        url = url.replace('ActivateWindow(%s' % launchID, 'ActivateWindow(10501')
        launchID = '10501'

    try:
        if url.startswith('__SF__'):
            url = url.replace('__SF__', '')

        if url.lower().startswith('playmedia'):
            xbmc.executebuiltin(url)
            return True, ''

        if url.lower().startswith('runscript'):
            xbmc.executebuiltin(url)
            return True, ''


        if url.lower().startswith('activatewindow'):
            import sys
            sfAddon = xbmcaddon.Addon(id = 'plugin.program.super.favourites')
            sfPath  = sfAddon.getAddonInfo('path')
            sys.path.insert(0, sfPath)

            import favourite
            import re
            import urllib

            original = re.compile('"(.+?)"').search(url).group(1)

            original = original.replace('%26', 'SF_AMP_SF') #protect '&' within parameters

            cmd = urllib.unquote_plus(original)

            try:    noFanart = favourite.removeFanart(cmd)
            except: pass

            try:    noFanart = favourite.removeSFOptions(cmd)
            except: pass

            if noFanart.endswith(os.path.sep):
               noFanart = noFanart[:-1]

            noFanart = noFanart.replace('+', '%2B')
            noFanart = noFanart.replace(' ', '+')

            url = url.replace(original, noFanart)
            url = url.replace('SF_AMP_SF', '%26') #put '&' back

            xbmc.executebuiltin(url)
            return True, ''

        import urllib
        params = url.split('?', 1)[-1]
        params = get_params(params)

        try:    mode = int(urllib.unquote_plus(params['mode']))
        except: return False, url

        if mode != 400:
            return False, url
        
        try:    path = urllib.unquote_plus(params['path'])
        except: path = None

        dirs = []
        if path:
            try:    current, dirs, files = os.walk(path).next()
            except: pass
            
            if len(dirs) == 0:
                import sys

                path = os.path.join(path, 'favourites.xml')

                sfAddon = xbmcaddon.Addon(id = 'plugin.program.super.favourites')
                sfPath  = sfAddon.getAddonInfo('path')

                sys.path.insert(0, sfPath)

                import favourite
                faves = favourite.getFavourites(path)

                if len(faves) == 1:
                    fave = faves[0][2]
                    if fave.lower().startswith('playmedia'):
                        import re
                        cmd = re.compile('"(.+?)"').search(fave).group(1)
                        return False, cmd

    except Exception, e:
        print str(e)
        pass

    url = 'ActivateWindow(%s,%s)' % (launchID, url)
    xbmc.executebuiltin(url)
    return True, ''
#---------------------------------------------------------------------------------------------------
def play(url, windowed, name=None):
    handled = False
    
    getIdle = int(ADDON.getSetting('idle').replace('Never', '0'))
    maxIdle = getIdle * 60 * 60

    dixie.SetSetting('streamURL', url)
 
    if 'tv/play_by_name_only/' in url or 'movies/play_by_name' in url:
        dixie.removeKepmap()
        xbmc.executebuiltin('XBMC.ActivateWindow(10025,%s)' % url)
#        while not xbmc.Player().isPlaying():
#            xbmc.sleep(1000)
        CheckIdle(maxIdle)
#        xbmc.sleep(2000)
#        wait(maxIdle)
#        dixie.loadKepmap()

    else:
        dixie.loadKepmap()
    # dixie.ShowBusy()
    
        if url.startswith('HDTV'):
            import hdtv
            delay  = 5
            stream = hdtv.getURL(url)
            
            if not playAndWait(stream, windowed, maxIdle, delay=delay):
                dixie.SetSetting('LOGIN_HDTV', '2001-01-01 00:00:00')
                stream = hdtv.getURL(url)
                playAndWait(stream, windowed, maxIdle, delay=delay)
            return

        if url.startswith('IPLAY'):
            import iplayer
            stream = iplayer.getURL(url)
            playAndWait(stream, windowed, maxIdle)
            return

        if url.startswith('IPTV:'):
            import iptv
            url = iptv.getURL(url)
            dixie.log(url)
            xbmc.executebuiltin('XBMC.RunPlugin(%s)' % url)
            return

        if url.startswith('UKTV'):
            import uktv
            stream = uktv.getURL(url)
            dixie.log(stream)
            playAndWait(stream, windowed, maxIdle)
            return
     
        if url.isdigit():
            command = ('{"jsonrpc": "2.0", "id":"1", "method": "Player.Open","params":{"item":{"channelid":%s}}}' % url)
            xbmc.executeJSONRPC(command)
            return
        
        if (url.startswith('__SF__')) or ('plugin://plugin.program.super.favourites' in url.lower()):
            handled, url = playSF(url)
            if handled:
                return


        if not checkForAlternateStreaming(url):
            playAndWait(url, windowed, maxIdle)

            xbmc.sleep(3000)
            if not xbmc.Player().isPlaying():
                # dixie.CloseBusy()
                xbmc.executebuiltin('XBMC.RunPlugin(%s)' % url)
                wait(maxIdle)
#---------------------------------------------------------------------------------------------------
def playAndWait(url, windowed, maxIdle, delay=0):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    playlist.add(url, xbmcgui.ListItem(''))
    try:
        xbmc.Player().play(playlist, windowed=windowed)
    except: pass

    if delay == 0:
        wait(maxIdle)
        return True

    delay *= 4
    while (delay >= 0) and (not xbmc.Player().isPlaying()):
        delay -= 1
        xbmc.sleep(250)

    if not xbmc.Player().isPlaying():
        return False
    
    wait(maxIdle)
    return True
#---------------------------------------------------------------------------------------------------
def wait(maxIdle):
    while xbmc.Player().isPlaying():
        xbmc.sleep(1000)
        CheckIdle(maxIdle)
#---------------------------------------------------------------------------------------------------
def checkForAlternateStreaming(url):
    if 'plugin.video.expattv' in url:
        return alternateStream(url)

    if 'plugin.video.filmon' in url:
        return alternateStream(url)

    if 'plugin.video.notfilmon' in url:
        return alternateStream(url)
        
    if 'plugin.video.itv' in url:        
        return alternateStream(url)
        
    if 'plugin.video.iplayerwww' in url:
        return alternateStream(url)
        
    # if 'plugin.video.uktvfrance' in url:
    #     return alternateStream(url)
        
    if 'plugin.video.muzu.tv' in url:        
        return alternateStream(url)
        
    if 'plugin.audio.ramfm' in url:        
        return alternateStream(url)
        
    if 'plugin.video.movie25' in url:
        return alternateStream(url)
        
    if 'plugin.video.irishtv' in url:
        return alternateStream(url)
        
    if 'plugin.video.F.T.V' in url:        
        return alternateStream(url)

    if 'plugin.video.sportsaholic' in url:        
        return alternateStream(url)
        
    if 'plugin.video.navi-x' in url:        
        return alternateStream(url)

    if 'plugin.video.mxnews' in url:        
        return alternateStream(url)

    if 'plugin.program.skygo.launcher' in url:        
        return alternateStream(url)

    if 'plugin.program.advanced.launcher' in url:        
        return alternateStream(url)

    if 'plugin.video.iplayer' in url:        
        return alternateStream(url)

    if 'plugin.video.stalker' in url:
        return alternateStream(url)

    if 'plugin.video.stealthplus' in url:
        return alternateStream(url)

    return False
#---------------------------------------------------------------------------------------------------
# Search text box
def Search(title, searchtext):
        keyboard = xbmc.Keyboard(searchtext, title)
        search_entered = ''
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_entered =  keyboard.getText()
            if search_entered == None:
                return False          
        return search_entered    
#---------------------------------------------------------------------------------------------------
def Edit_Search(channel, repository, plugin, playertype, channelorig, name):
    newname = Search('Edit Channel Name', channel)
    newarray = newname+'|'+repository+'|'+plugin+'|'+playertype+'|'+channelorig+'|'+name
    metalliq_play(newarray)
#---------------------------------------------------------------------------------------------------
def Edit_SF_Name(status, playertype, channelorig, name):
    SF_Path  = os.path.join(SF_CHANNELS, '-metalliq', channelorig, 'favourites.xml')
    readfile = open(SF_Path, 'r')
    content  = readfile.read()
    readfile.close()

    writefile = open(SF_Path, 'w')
# If playback worked mark with a tick
    if status == 'good':
        if name.startswith('[COLOR=red][B](X)[/B] [/COLOR]'):
            tempname   = name.replace('[COLOR=red][B](X)[/B] [/COLOR]', '[COLOR=lime][B](+)[/B] [/COLOR]')
            content = content.replace(name, tempname)
        elif not name.startswith('[COLOR=lime][B](+)[/B] [/COLOR]'):
            tempname   = '[COLOR=lime][B](+)[/B] [/COLOR]'+name
            content = content.replace(name, tempname)

# If playback failed mark with a cross
    if status == 'bad':
        if name.startswith('[COLOR=lime][B](+)[/B] [/COLOR]'):
            tempname   = name.replace('[COLOR=lime][B](+)[/B] [/COLOR]', '[COLOR=red][B](X)[/B] [/COLOR]')
            content = content.replace(name, tempname)
        elif not name.startswith('[COLOR=red][B](X)[/B] [/COLOR]'):
            tempname   = '[COLOR=red][B](X)[/B] [/COLOR]'+name
            content = content.replace(name, tempname)

    writefile.write(content)
    writefile.close()
    xbmc.executebuiltin('Container.Refresh')
#---------------------------------------------------------------------------------------------------
def alternateStream(url):
    # dixie.CloseBusy()
    xbmc.executebuiltin('XBMC.RunPlugin(%s)' % url)
    print '***** tvp alternateStream *****', url
    
    retries = 10
    while retries > 0 and not xbmc.Player().isPlaying():
        retries -= 1
        xbmc.sleep(1000)
        
    return True
#---------------------------------------------------------------------------------------------------
def metalliq_play(args):
    run        = 0
    stop       = 0
    windowopen = 0
    xbmc.log('### metalliq play args: %s' % args)
    channel, repository, plugin, playertype, channel_orig, itemname = args.split('|')
    dixie.log('### %s' % channel)
    dixie.log('### %s' % repository)
    dixie.log('### %s' % plugin)
    dixie.log('### %s' % playertype)
    try:
        addonid         = xbmcaddon.Addon(id=plugin)
        addonname       = addonid.getAddonInfo('name')
        updateicon      = os.path.join(ADDONS, plugin, 'icon.png')
        xbmc.executebuiltin("XBMC.Notification(Please Wait...,Searching for  [COLOR=dodgerblue]"+channel+"[/COLOR] ,5000,"+updateicon+")")
        xbmc.executebuiltin('RunPlugin(plugin://plugin.video.metalliq/live/%s/None/en/%s)' % (channel, playertype))
    except:
        try:
            repoid          = xbmcaddon.Addon(id=repository)
            reponame        = repoid.getAddonInfo('name')
            run             = 1
        except:
            if dialog.yesno('Repository Install', 'To install the add-on required you need the following repo:','[COLOR=dodgerblue]%s[/COLOR]' % repository,'Would you like to install?'):
                dp.create('Downloading','[COLOR=dodgerblue]%s[/COLOR]' % repository,'Please Wait')
                DOWNLOAD_ZIP = os.path.join(PACKAGES, repository+'.zip')
                download.download('https://github.com/noobsandnerds/noobsandnerds/blob/master/zips/%s/%s-0.0.0.1.zip?raw=true' % (repository, repository), DOWNLOAD_ZIP, dp)
                extract.all(DOWNLOAD_ZIP, ADDONS, dp)
                dp.close()
                xbmc.executebuiltin('UpdateLocalAddons')
                xbmc.executebuiltin('UpdateAddonRepos')
                xbmc.sleep(2000)
                counter = 0
                while not run and counter < 10:
                    try:
                        reponame = repoid.getAddonInfo('name')
                        run = 1
                    except:
                        xbmc.sleep(1000)
                        counter += 1
                if counter == 10:
                    dialog.ok('Possible problem detected', 'There may have been a problem installing this repository, please click on the item again.')

    if run == 1:
        xbmc.executebuiltin("ActivateWindow(10025,plugin://%s,return)" % plugin)
        xbmc.sleep(1500)
        activewindow = True
        while activewindow:
            activewindow = xbmc.getCondVisibility('Window.IsActive(yesnodialog)')
        xbmc.sleep(500)
        activewindow = xbmc.getCondVisibility('Window.IsActive(progressdialog)')
        while activewindow:
            activewindow = xbmc.getCondVisibility('Window.IsActive(progressdialog)')
        xbmc.sleep(500)
        activewindow = xbmc.getCondVisibility('Window.IsActive(textviewer)')
        if activewindow:
            windowopen = 1
        while activewindow:
            activewindow = xbmc.getCondVisibility('Window.IsActive(textviewer)')
        if windowopen:
            xbmc.executebuiltin('Action(BACK)')
        xbmc.sleep(300)
        xbmc.executebuiltin('Action(BACK)')
        updateicon      = os.path.join(ADDONS, plugin, 'icon.png')
        xbmc.executebuiltin("XBMC.Notification(Please Wait...,Searching for  [COLOR=dodgerblue]"+channel+"[/COLOR] ,5000,"+updateicon+")")
        xbmc.executebuiltin('RunPlugin(plugin://plugin.video.metalliq/live/%s/None/en/%s)' % (channel, playertype))

# Check if playback works
        while stop == 0:
            okwindow = xbmc.getCondVisibility('Window.IsActive(okdialog)')
            if okwindow:
                while okwindow:
                    okwindow = xbmc.getCondVisibility('Window.IsActive(okdialog)')
                stop = 2
                xbmc.log('stop == 2')
            player   = xbmc.getCondVisibility('Player.Playing')
            if player:
                stop = 3
        if stop == 2:
            if dialog.yesno('Edit Search Term?','Would you like to edit the channel name? It may be this add-on has a slightly different spelling of [COLOR=dodgerblue]%s[/COLOR]' % channel):
                Edit_Search(channel, repository, plugin, playertype, channel_orig, itemname)
            else:
                Edit_SF_Name('bad', playertype, channel_orig, itemname)
        if stop == 3:
            Edit_SF_Name('good', playertype, channel_orig, itemname)
#---------------------------------------------------------------------------------------------------
args = sys.argv[1]
if '|' in args:
    metalliq_play(args)

elif __name__ == '__main__':
    name = None
    if len(sys.argv) > 3:
        name = sys.argv[3]
    
    play(sys.argv[1], sys.argv[2] == 1, name)
