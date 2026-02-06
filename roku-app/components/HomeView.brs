sub init()
  m.tabBar = m.top.findNode("tabBar")
  m.liveGrid = m.top.findNode("liveGrid")
  m.moviesGrid = m.top.findNode("moviesGrid")
  m.seriesGrid = m.top.findNode("seriesGrid")
  m.statusPanel = m.top.findNode("statusPanel")
  m.refreshPanel = m.top.findNode("refreshPanel")
  m.refreshButton = m.top.findNode("refreshButton")
  m.detailView = m.top.findNode("detailView")
  m.refreshModal = m.top.findNode("refreshModal")
  m.toast = m.top.findNode("toast")
  m.refreshTimer = m.top.findNode("refreshTimer")
  m.toastTimer = m.top.findNode("toastTimer")

  m.activeTab = "Live TV"
  m.tabBar.observeField("selectedTab", "onTabChanged")
  m.liveGrid.observeField("selectedItem", "onItemSelected")
  m.moviesGrid.observeField("selectedItem", "onItemSelected")
  m.seriesGrid.observeField("selectedItem", "onItemSelected")
  m.refreshTimer.observeField("fire", "onRefreshComplete")
  m.toastTimer.observeField("fire", "onToastComplete")

  m.liveGrid.gridContent = buildSampleGrid("Live")
  m.moviesGrid.gridContent = buildSampleGrid("Movies")
  m.seriesGrid.gridContent = buildSampleGrid("Series")

  m.tabBar.setFocus(true)
end sub

function onKeyEvent(key as String, press as Boolean) as Boolean
  if press = false then return false

  if m.detailView.visible
    if key = "back"
      m.detailView.visible = false
      m.tabBar.setFocus(true)
      return true
    else if key = "OK"
      m.top.requestPlayback = true
      return true
    end if
  end if

  if key = "back"
    return true
  end if

  if key = "OK" and m.activeTab = "Refresh"
    startRefresh()
    return true
  end if

  return false
end function

sub onTabChanged()
  m.activeTab = m.tabBar.selectedTab
  m.liveGrid.visible = (m.activeTab = "Live TV")
  m.moviesGrid.visible = (m.activeTab = "Movies")
  m.seriesGrid.visible = (m.activeTab = "Series")
  m.statusPanel.visible = (m.activeTab = "Status")
  m.refreshPanel.visible = (m.activeTab = "Refresh")

  if m.refreshPanel.visible
    m.refreshButton.setFocus(true)
  else
    m.tabBar.setFocus(true)
  end if
end sub

sub onItemSelected()
  if m.activeTab = "Live TV"
    item = m.liveGrid.selectedItem
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
  end if
end sub

sub startRefresh()
  m.refreshModal.visible = true
  m.refreshTimer.control = "start"
end sub

sub onRefreshComplete()
  m.refreshModal.visible = false
  m.toast.message = "Refresh complete – updated at 09:45"
  m.toast.visible = true
  m.toastTimer.control = "start"
end sub

sub onToastComplete()
  m.toast.visible = false
end sub

function buildSampleGrid(prefix as String) as Object
  root = CreateObject("roSGNode", "ContentNode")
  categories = ["Featured", "Action", "Comedy"]
  for each category in categories
    row = CreateObject("roSGNode", "ContentNode")
    row.title = category
    for i = 1 to 10
      item = CreateObject("roSGNode", "ContentNode")
      item.title = prefix + " " + category + " " + i.ToStr()
      item.description = "Sample description for " + item.title
      item.duration = "120 min"
      item.genre = category
      item.rating = "PG-13"
      row.appendChild(item)
    end for
    root.appendChild(row)
  end for
  return root
end function
