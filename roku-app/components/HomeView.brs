sub init()
  m.tabBar = m.top.findNode("tabBar")
  m.liveGrid = m.top.findNode("liveGrid")
  m.tvGrid = m.top.findNode("tvGrid")
  m.moviesGrid = m.top.findNode("moviesGrid")
  m.seriesGrid = m.top.findNode("seriesGrid")
  m.statusPanel = m.top.findNode("statusPanel")
  m.refreshLink = m.statusPanel.findNode("refreshLink")
  m.lastRefreshLabel = m.statusPanel.findNode("lastRefreshLabel")
  m.detailView = m.top.findNode("detailView")
  m.refreshModal = m.top.findNode("refreshModal")
  m.toast = m.top.findNode("toast")
  m.refreshTimer = m.top.findNode("refreshTimer")
  m.progressTimer = m.top.findNode("progressTimer")
  m.toastTimer = m.top.findNode("toastTimer")

  m.progressFill = m.refreshModal.findNode("progressFill")
  m.progressLabel = m.refreshModal.findNode("progressLabel")
  m.progressBarWidth = 320
  m.refreshProgress = 0.0
  m.refreshStart = invalid
  m.refreshDurationSec = m.refreshTimer.duration

  m.activeTab = "Live"
  m.focusArea = "tabs"
  m.refreshInProgress = false
  m.tabBar.observeField("selectedTab", "onTabChanged")
  m.liveGrid.observeField("selectedItem", "onItemSelected")
  m.tvGrid.observeField("selectedItem", "onItemSelected")
  m.moviesGrid.observeField("selectedItem", "onItemSelected")
  m.seriesGrid.observeField("selectedItem", "onItemSelected")
  m.refreshTimer.observeField("fire", "onRefreshComplete")
  m.progressTimer.observeField("fire", "onProgressTick")
  m.toastTimer.observeField("fire", "onToastComplete")

  m.liveGrid.gridContent = buildSampleList("Live")
  m.tvGrid.gridContent = buildSampleList("TV")
  m.moviesGrid.gridContent = buildSampleList("Movies")
  m.seriesGrid.gridContent = buildSampleList("Series")

  m.tabBar.setFocus(true)
end sub

function onKeyEvent(key as String, press as Boolean) as Boolean
  if press = false then return false
  if m.refreshInProgress then return true

  if m.detailView.visible
    if key = "back"
      m.detailView.visible = false
      m.tabBar.setFocus(true)
      m.focusArea = "tabs"
      return true
    else if key = "OK"
      m.top.requestPlayback = true
      return true
    end if
  end if

  if key = "back"
    return true
  end if

  if key = "down"
    if m.focusArea = "tabs"
      setFocusArea("list")
      return true
    end if
  else if key = "up"
    if m.focusArea = "list"
      setFocusArea("tabs")
      return true
    end if
  else if key = "right"
    if m.focusArea <> "status"
      setFocusArea("status")
      return true
    end if
  else if key = "left"
    if m.focusArea = "status"
      setFocusArea("list")
      return true
    end if
  else if key = "OK" and m.focusArea = "status"
    startRefresh()
    return true
  end if

  return false
end function

sub onTabChanged()
  m.activeTab = m.tabBar.selectedTab
  m.liveGrid.visible = (m.activeTab = "Live")
  m.tvGrid.visible = (m.activeTab = "TV")
  m.moviesGrid.visible = (m.activeTab = "Movies")
  m.seriesGrid.visible = (m.activeTab = "Series")
  m.tabBar.setFocus(true)
  m.focusArea = "tabs"
end sub

sub onItemSelected()
  if m.activeTab = "Live"
    item = m.liveGrid.selectedItem
  else if m.activeTab = "TV"
    item = m.tvGrid.selectedItem
  else if m.activeTab = "Movies"
    item = m.moviesGrid.selectedItem
  else if m.activeTab = "Series"
    item = m.seriesGrid.selectedItem
  else
    item = invalid
  end if

  if item <> invalid
    m.detailView.contentItem = item
    m.detailView.visible = true
    m.detailView.setFocus(true)
    m.focusArea = "detail"
  end if
end sub

sub startRefresh()
  if m.refreshInProgress then return
  m.refreshInProgress = true
  m.refreshLink.enabled = false
  m.lastRefreshLabel.text = "Dernier refresh: en cours..."
  m.refreshModal.visible = true

  m.refreshProgress = 0.0
  updateProgressUI(0.0)
  m.refreshStart = CreateObject("roTimespan")
  m.progressTimer.control = "start"

  m.refreshTimer.control = "start"
end sub

sub onRefreshComplete()
  m.progressTimer.control = "stop"
  updateProgressUI(1.0)

  m.refreshModal.visible = false
  m.refreshInProgress = false
  m.refreshLink.enabled = true
  m.lastRefreshLabel.text = "Dernier refresh: " + getCurrentTime()
  m.toast.message = "Refresh termine - " + getCurrentTime()
  m.toast.visible = true
  m.toastTimer.control = "start"
end sub

sub onProgressTick()
  if m.refreshStart = invalid then return
  elapsedMs = m.refreshStart.TotalMilliseconds()
  progress = elapsedMs / (m.refreshDurationSec * 1000.0)
  if progress > 0.95 then progress = 0.95
  updateProgressUI(progress)
end sub

sub updateProgressUI(progress as Float)
  if m.progressFill <> invalid
    width = Int(m.progressBarWidth * progress)
    m.progressFill.width = width
  end if
  if m.progressLabel <> invalid
    pct = Int(progress * 100)
    m.progressLabel.text = "Progress: " + pct.ToStr() + "%"
  end if
end sub

sub onToastComplete()
  m.toast.visible = false
end sub

sub setFocusArea(area as String)
  m.focusArea = area
  if area = "tabs"
    m.tabBar.setFocus(true)
  else if area = "list"
    if m.activeTab = "Live"
      m.liveGrid.setFocus(true)
    else if m.activeTab = "TV"
      m.tvGrid.setFocus(true)
    else if m.activeTab = "Movies"
      m.moviesGrid.setFocus(true)
    else if m.activeTab = "Series"
      m.seriesGrid.setFocus(true)
    end if
  else if area = "status"
    m.refreshLink.setFocus(true)
  end if
end sub

function getCurrentTime() as String
  now = CreateObject("roDateTime")
  hours = now.GetHours().ToStr()
  minutes = now.GetMinutes().ToStr()
  if minutes.len() = 1 then minutes = "0" + minutes
  return hours + ":" + minutes
end function

function buildSampleList(prefix as String) as Object
  root = CreateObject("roSGNode", "ContentNode")
  for i = 1 to 18
    item = CreateObject("roSGNode", "ContentNode")
    item.title = prefix + " " + i.ToStr()
    item.description = "Selection " + prefix + " avec lecture instantanee."
    item.duration = "120 min"
    item.genre = prefix
    item.rating = "PG-13"
    root.appendChild(item)
  end for
  return root
end function
