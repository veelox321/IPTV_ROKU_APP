sub init()
  m.tabList = m.top.findNode("tabList")
  m.tabs = ["Live", "TV", "Movies", "Series"]
  m.tabList.content = buildTabs(m.tabs)
  m.tabList.observeField("itemSelected", "onItemSelected")
  m.tabList.setFocus(true)
end sub

sub onItemSelected()
  index = m.tabList.itemSelected
  if index >= 0 and index < m.tabs.count()
    m.top.selectedTab = m.tabs[index]
  end if
end sub

function buildTabs(labels as Object) as Object
  root = CreateObject("roSGNode", "ContentNode")
  for each label in labels
    tab = CreateObject("roSGNode", "ContentNode")
    tab.title = label
    root.appendChild(tab)
  end for
  return root
end function
