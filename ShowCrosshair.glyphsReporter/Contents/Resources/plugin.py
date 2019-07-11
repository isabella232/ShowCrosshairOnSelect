# encoding: utf-8

###########################################################################################################
#
#
#	Reporter Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Reporter
#
#
###########################################################################################################

from GlyphsApp import *
from GlyphsApp.plugins import *
from GlyphsApp.plugins import setUpMenuHelper
import math

class ShowCrosshair(ReporterPlugin):

	def settings(self):
		self.menuName = Glyphs.localize({
			'en': u'Crosshair', 
			'de': u'Fadenkreuz',
			'es': u'cruz',
			'fr': u'réticule',
			'jp': u'カーソル照準',
		})
		NSUserDefaults.standardUserDefaults().registerDefaults_({
				"com.mekkablue.ShowCrosshair.universalCrosshair": 1,
				"com.mekkablue.ShowCrosshair.showCoordinates": 0,
				"com.mekkablue.ShowCrosshair.fontSize": 10.0
			})
		# self.universalCrosshair = bool( Glyphs.defaults["com.mekkablue.ShowCrosshair.universalCrosshair"] )
		self.controller = None
	
	def foreground(self, layer):
		toolEventHandler = self.controller.view().window().windowController().toolEventHandler()
		toolIsDragging = toolEventHandler.dragging()
		toolIsTextTool = toolEventHandler.className() == "GlyphsToolText"
		shouldDisplay = (bool(Glyphs.defaults["com.mekkablue.ShowCrosshair.universalCrosshair"]) and not toolIsTextTool) or toolIsDragging
		
		if Glyphs.boolDefaults["com.mekkablue.ShowCrosshair.showThickness"] and shouldDisplay:
			font = Glyphs.font
			master = layer.associatedFontMaster()
			scale = self.getScale()
			mousePosition = self.mousePosition()

			# stem thickness horizontal slice
			sliceY = mousePosition.y
			minX = -1000*(font.upm/1000.0)
			maxX = layer.width + 1000*(font.upm/1000.0)
			prev = minX
			xs = {}
			for inter in layer.calculateIntersectionsStartPoint_endPoint_decompose_(
				(minX,sliceY),
				(maxX,sliceY),
				True,
				):
				if prev != minX and inter.x != maxX:
					xs[(inter.x-prev)/2+prev] = inter.x-prev
				prev = inter.x
			
			# stem thickness vertical slice
			sliceX = mousePosition.x
			minY = master.descender - 1000*(font.upm/1000.0)
			maxY = master.ascender  + 1000*(font.upm/1000.0)
			prev = minY
			ys = {}
			verticalIntersections = layer.calculateIntersectionsStartPoint_endPoint_decompose_(
				self.italicize( NSPoint(sliceX,minY), italicAngle=master.italicAngle, pivotalY=sliceY ),
				self.italicize( NSPoint(sliceX,maxY), italicAngle=master.italicAngle, pivotalY=sliceY ),
				True,
				)
			for inter in verticalIntersections:
				if prev != minY and inter.y != maxY:
					ys[(inter.y-prev)/2+prev] = inter.y-prev
				prev = inter.y

			# set font attributes
			fontSize = Glyphs.defaults["com.mekkablue.ShowCrosshair.fontSize"]
			thicknessFontAttributes = { 
				NSFontAttributeName: NSFont.monospacedDigitSystemFontOfSize_weight_(fontSize/scale,0.0),
				NSForegroundColorAttributeName: NSColor.textColor()
			}
			
			# number badges on vertical slice:
			for key, item in ys.iteritems():
				item = round(item, 1)
				if item != 0:
					x, y = sliceX, key
					# adjust x for italic angle if necessary:
					if master.italicAngle:
						x = self.italicize( NSPoint(x,y), italicAngle=master.italicAngle, pivotalY=sliceY ).x
					self.drawThicknessBadge(scale, fontSize, x, y, item)
					self.drawThicknessText(thicknessFontAttributes, x, y, item)
					
			# number badges on horizontal slice:
			for key, item in xs.iteritems():
				item = round(item, 1)
				if item != 0:
					x, y = key, sliceY
					self.drawThicknessBadge(scale, fontSize, x, y, item)
					self.drawThicknessText(thicknessFontAttributes, x, y, item)
	
	def italicize( self, thisPoint, italicAngle=0.0, pivotalY=0.0 ):
		"""
		Returns the italicized position of an NSPoint 'thisPoint'
		for a given angle 'italicAngle' and the pivotal height 'pivotalY',
		around which the italic slanting is executed, usually half x-height.
		Usage: myPoint = italicize(myPoint,10,xHeight*0.5)
		"""
		x = thisPoint.x
		yOffset = thisPoint.y - pivotalY # calculate vertical offset
		italicAngle = math.radians( italicAngle ) # convert to radians
		tangens = math.tan( italicAngle ) # math.tan needs radians
		horizontalDeviance = tangens * yOffset # vertical distance from pivotal point
		x += horizontalDeviance # x of point that is yOffset from pivotal point
		return NSPoint( x, thisPoint.y )
	
		
	def background(self, layer):
		toolEventHandler = self.controller.view().window().windowController().toolEventHandler()
		toolIsDragging = toolEventHandler.dragging()
		toolIsTextTool = toolEventHandler.className() == "GlyphsToolText"
		crossHairCenter = self.mousePosition()
		shouldDisplay = (bool(Glyphs.defaults["com.mekkablue.ShowCrosshair.universalCrosshair"]) and not toolIsTextTool) or toolIsDragging
		
		if crossHairCenter.x < NSNotFound and shouldDisplay:
			# determine italic angle:
			italicAngle = 0.0
			try:
				thisMaster = layer.associatedFontMaster()
				italicAngle = thisMaster.italicAngle
			except:
				pass
			
			# set up bezierpath:
			offset = 1000000
			NSColor.disabledControlTextColor().set() # subtle grey
			crosshairPath = NSBezierPath.bezierPath()
			crosshairPath.setLineWidth_( 0.75 / self.getScale() )

			# vertical line:
			crosshairPath.moveToPoint_( self.italicize( NSPoint(crossHairCenter.x,-offset), italicAngle=italicAngle, pivotalY=crossHairCenter.y) )
			crosshairPath.lineToPoint_( self.italicize( NSPoint(crossHairCenter.x,+offset), italicAngle=italicAngle, pivotalY=crossHairCenter.y) )
			
			# horizontal line:
			crosshairPath.moveToPoint_( NSPoint(-offset,crossHairCenter.y) )
			crosshairPath.lineToPoint_( NSPoint(+offset,crossHairCenter.y) )

			# execute stroke:
			crosshairPath.stroke()
	
	def mousePosition(self):
		view = self.controller.graphicView()
		mousePosition = view.getActiveLocation_(Glyphs.currentEvent())
		return mousePosition
	
	def foregroundInViewCoords(self, layer):
		toolEventHandler = self.controller.view().window().windowController().toolEventHandler()
		toolIsTextTool = toolEventHandler.className() == "GlyphsToolText"

		if Glyphs.boolDefaults["com.mekkablue.ShowCrosshair.showCoordinates"] and not toolIsTextTool:
			mousePosition = self.mousePosition()
			coordinateText = "%4d, %4d" % (
				round(mousePosition.x), 
				round(mousePosition.y)
			)
			
			fontSize = Glyphs.defaults["com.mekkablue.ShowCrosshair.fontSize"]
			fontAttributes = { 
				#NSFontAttributeName: NSFont.labelFontOfSize_(10.0),
				NSFontAttributeName: NSFont.monospacedDigitSystemFontOfSize_weight_(fontSize,0.0),
				NSForegroundColorAttributeName: NSColor.textColor()
			}
			displayText = NSAttributedString.alloc().initWithString_attributes_(
				unicode(coordinateText), 
				fontAttributes
			)
			textAlignment = 0 # top left: 6, top center: 7, top right: 8, center left: 3, center center: 4, center right: 5, bottom left: 0, bottom center: 1, bottom right: 2
			#font = layer.parent.parent
			lowerLeftCorner = self.controller.viewPort.origin
			displayText.drawAtPoint_alignment_(lowerLeftCorner, textAlignment)

	def drawThicknessBadge(self, scale, fontSize, x, y, value):
		width = len(str(value)) * fontSize * 0.7 / scale
		rim = fontSize * 0.3 / scale
		badge = NSRect()
		badge.origin = NSPoint( x-width/2, y-fontSize/2-rim )
		badge.size = NSSize( width, fontSize + rim*2 )
		NSColor.textBackgroundColor().set()
		NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_( badge, fontSize*0.5, fontSize*0.5 ).fill()

	def drawThicknessText(self, thicknessFontAttributes, x, y, item):
		displayText = NSAttributedString.alloc().initWithString_attributes_(
			unicode(item), 
			thicknessFontAttributes
		)
		displayText.drawAtPoint_alignment_((x, y), 4)


	def mouseDidMove(self, notification):
		if self.controller:
			self.controller.redraw()
		else:
			Glyphs.redraw()

	def willActivate(self):
		Glyphs.addCallback(self.mouseDidMove, MOUSEMOVED)
		
	def willDeactivate(self):
		try:
			Glyphs.removeCallback(self.mouseDidMove, MOUSEMOVED)
		except:
			import traceback
			NSLog(traceback.format_exc())
	
	def toggleUniversalCrosshair(self):
		self.toggleSetting("universalCrosshair")
		
	def toggleShowCoordinates(self):
		self.toggleSetting("showCoordinates")

	def toggleShowThickness(self):
		self.toggleSetting("showThickness")
	
	def conditionalContextMenus(self):
		return [
		{
			'name': Glyphs.localize({
				'en': u"Crosshair Options:", 
				'de': u"Fadenkreuz-Einstellungen:", 
				'es': u"Opciones de la cruz:", 
				'fr': u"Options pour le réticule:",
				'jp': u"照準プラグインオプション",
				}), 
			'action': None,
		},
		{
			'name': Glyphs.localize({
				'en': u"Always Show Crosshair", 
				'de': u"Fadenkreuz immer anzeigen", 
				'es': u"Siempre mostrar la cruz", 
				'fr': u"Toujours afficher le réticule",
				'jp': u"照準を常に表示",
				}), 
			'action': self.toggleUniversalCrosshair,
			'state': Glyphs.defaults[ "com.mekkablue.ShowCrosshair.universalCrosshair" ],
		},
		{
			'name': Glyphs.localize({
				'en': u"Show Coordinates", 
				'de': u"Koordinaten anzeigen", 
				'es': u"Mostrar coordinados", 
				'fr': u"Afficher les coordonnées",
				'jp': u"マウスの座標を左下に表示",
				}), 
			'action': self.toggleShowCoordinates,
			'state': Glyphs.defaults[ "com.mekkablue.ShowCrosshair.showCoordinates" ],
		},
		{
			'name': Glyphs.localize({
				'en': u"Show Thicknesses", 
				'de': u"Dicken anzeigen", 
				'es': u"Mostrar grosores", 
				'fr': u"Afficher les épaisseurs",
				'jp': u"縦横の太さを表示",
				}), 
			'action': self.toggleShowThickness,
			'state': Glyphs.defaults[ "com.mekkablue.ShowCrosshair.showThickness" ],
		},
		]
	
	def toggleSetting(self, prefName):
		pref = "com.mekkablue.ShowCrosshair.%s" % prefName
		oldSetting = bool(Glyphs.defaults[pref])
		Glyphs.defaults[pref] = int(not oldSetting)
	
	def addMenuItemsForEvent_toMenu_(self, event, contextMenu):
		'''
		The event can tell you where the user had clicked.
		'''
		try:
			
			if self.generalContextMenus:
				setUpMenuHelper(contextMenu, self.generalContextMenus, self)
			
			newSeparator = NSMenuItem.separatorItem()
			contextMenu.addItem_(newSeparator)
			
			contextMenus = self.conditionalContextMenus()
			if contextMenus:
				setUpMenuHelper(contextMenu, contextMenus, self)
		
		except:
			import traceback
			NSLog(traceback.format_exc())
	