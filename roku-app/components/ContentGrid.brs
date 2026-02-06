sub init()
  m.list = m.top.findNode("list")
  m.list.observeField("itemSelected", "onItemSelected")
  m.top.observeField("gridContent", "onGridContent")
end sub

sub onGridContent()
  m.list.content = m.top.gridContent
end sub

sub onItemSelected()
  index = m.list.itemSelected
  if index < 0 then return
  selected = m.list.content.getChild(index)
  if selected <> invalid
    m.top.selectedItem = selected
  end if
end sub
