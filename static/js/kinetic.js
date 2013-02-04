/**
 * KineticJS JavaScript Library v3.6.4
 * http://www.kineticjs.com/
 * Copyright 2012, Eric Rowell
 * Licensed under the MIT or GPL Version 2 licenses.
 * Date: Jan 29 2012
 *
 * Copyright (C) 2011 - 2012 by Eric Rowell
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */
///////////////////////////////////////////////////////////////////////
//  Global Object
///////////////////////////////////////////////////////////////////////
var Kinetic = {};
Kinetic.GlobalObject = {
    stages: [],
    shapeIdCounter: 0,
    bind: function(eventListeners, typesStr, handler){
        var types = typesStr.split(" ");
        /*
         * loop through types and attach event listeners to
         * each one.  eg. "click mouseover.namespace mouseout"
         * will create three event bindings
         */
        for (var n = 0; n < types.length; n++) {
            var type = types[n];
            var event = (type.indexOf('touch') == -1) ? 'on' + type : type;
            var parts = event.split(".");
            var baseEvent = parts[0];
            var name = parts.length > 1 ? parts[1] : "";
            
            if (!eventListeners[baseEvent]) {
                eventListeners[baseEvent] = [];
            }
            
            eventListeners[baseEvent].push({
                name: name,
                handler: handler
            });
        }
    },
    unbind: function(eventListeners, typesStr){
        var types = typesStr.split(" ");
        
        for (var n = 0; n < types.length; n++) {
            var type = types[n];
            var event = (type.indexOf('touch') == -1) ? 'on' + type : type;
            var parts = event.split(".");
            var baseEvent = parts[0];
            
            if (eventListeners[baseEvent] && parts.length > 1) {
                var name = parts[1];
                
                for (var i = 0; i < eventListeners[baseEvent].length; i++) {
                    if (eventListeners[baseEvent][i].name == name) {
                        eventListeners[baseEvent].splice(i, 1);
                        if (eventListeners[baseEvent].length === 0) {
                            eventListeners[baseEvent] = undefined;
                        }
                        break;
                    }
                }
            }
            else {
                eventListeners[baseEvent] = undefined;
            }
        }
    },
    handleEvents: function(shape, eventType, evt){
        // generic events handler
        function handle(obj){
            var el = obj.eventListeners;
            if (el[eventType]) {
                var events = el[eventType];
                for (var i = 0; i < events.length; i++) {
                    events[i].handler.apply(obj, [evt]);
                }
            }
        }
        /*
         * simulate bubbling by handling shape events
         * first, followed by group events, followed
         * by layer events
         */
        handle(shape);
        handle(shape.layer);
    }
};

///////////////////////////////////////////////////////////////////////
//  Link
///////////////////////////////////////////////////////////////////////
/**
 * Link constructor
 * @param {Shape} shape
 */
Kinetic.Link = function(shape){
    this.shape = shape;
    shape.link = this;
    this.id = shape.id;
    this.index = undefined;
    
    // thes params are string ids
    this.nextId = undefined;
    this.prevId = undefined;
};

///////////////////////////////////////////////////////////////////////
//  Layer
///////////////////////////////////////////////////////////////////////
/**
 * Layer constructor
 * @param {string} name
 */
Kinetic.Layer = function(name){
    this.name = name;
    this.shapeIndexCounter = 0;
    this.isListening = true;
    this.shapeNames = {};
    this.eventListeners = {};
    this.visible = true;
    this.canvas = document.createElement('canvas');
    this.context = this.canvas.getContext('2d');
    this.canvas.style.position = 'absolute';
    
    //links is an array of links which point to event links
    this.links = [];
    this.linkHash = {};
    
    this.headId = undefined;
    this.tailId = undefined;
};
/*
 * Layer methods
 */
Kinetic.Layer.prototype = {
    /**
     * listen or don't listen to events
     * @param {boolean} isListening
     */
    listen: function(isListening){
        this.isListening = isListening;
    },
    /**
     * clear layer
     */
    clear: function(){
        var context = this.getContext();
        var canvas = this.getCanvas();
        context.clearRect(0, 0, canvas.width, canvas.height);
    },
    /**
     * get layer canvas
     */
    getCanvas: function(){
        return this.canvas;
    },
    /**
     * get layer context
     */
    getContext: function(){
        return this.context;
    },
    /**
     * get shapes
     */
    getShapes: function(){
        var shapes = [];
        for (var n = 0; n < this.links.length; n++) {
            shapes.push(this.links[n].shape);
        }
        return shapes;
    },
    /**
     * get zIndex
     */
    getZIndex: function(){
        return this.index;
    },
    /**
     * draw all shapes in layer
     */
    draw: function(){
        this.clear();
        if (this.visible) {
            var links = this.links;
            for (var n = 0; n < links.length; n++) {
                var shape = links[n].shape;
                shape.draw(shape.layer);
            }
        }
    },
    /**
     * add link to links hash
     * @param {Link} link
     */
    addLink: function(link){
        var shape = link.shape;
        shape.layer = this;
        // add link to array
        this.links.push(link);
        // add link to hash
        this.linkHash[link.id] = link;
        link.index = this.links.length - 1;
        
        if (shape.isListening) {
            // if tail doesnt exist, add tail and head
            if (this.tailId === undefined) {
                this.tailId = link.id;
                this.headId = link.id;
            }
            // if tail does exist, this means there's at least one link
            else {
                var tail = this.linkHash[this.tailId];
                tail.nextId = link.id;
                link.prevId = tail.id;
                this.tailId = link.id;
            }
        }
    },
    /**
     * bind event listener to all shapes in layer
     * @param {string} typesStr
     * @param {function} handler
     */
    on: function(typesStr, handler){
        Kinetic.GlobalObject.bind(this.eventListeners, typesStr, handler);
    },
    /**
     * remove event listener
     * @param {string} typesStr
     */
    off: function(typesStr){
        Kinetic.GlobalObject.unbind(this.eventListeners, typesStr);
    },
    /**
     * show layer
     */
    show: function(){
        this.visible = true;
    },
    /**
     * hide layer
     */
    hide: function(){
        this.visible = false;
    },
    /**
     * add shape to layer
     * @param {Shape} shape
     */
    add: function(shape){
        if (shape.name) {
            this.shapeNames[shape.name] = shape;
        }
        shape.id = Kinetic.GlobalObject.shapeIdCounter++;
        var link = new Kinetic.Link(shape);
        this.addLink(link);
    },
    /**
     * get shape by name
     * @param {string} name
     */
    getShape: function(name){
        return this.shapeNames[name];
    },
    /**
     * remove a shape from the layer
     * @param {Shape} shape
     */
    remove: function(shape){
        var link = shape.link;
        this.removeLink(link);
        link = null;
        shape = null;
    },
    /**
     * remove link from layer
     * @param {Link} link
     */
    removeLink: function(link){
        link.shape.layer = undefined;
        this.unlink(link);
        this.links.splice(link.index, 1);
        this.linkHash[link.id] = undefined;
        this.setLinkIndices();
    },
    
    /**
     * unlink link.  This is different from removeLink because it
     * keeps the link in the layer data structure
     * @param {Link} link
     */
    unlink: function(link){
        // set head if needed
        if (link.id === this.headId) {
            this.headId = link.nextId;
        }
        // set tail if needed
        if (link.id === this.tailId) {
            this.tailId = link.prevId;
        }
        // link prev to next
        if (link.prevId !== undefined) {
            this.linkHash[link.prevId].nextId = link.nextId;
        }
        if (link.nextId !== undefined) {
            this.linkHash[link.nextId].prevId = link.prevId;
        }
        // clear pointers
        link.prevId = undefined;
        link.nextId = undefined;
    },
    /**
     * link link2 after link1.  link1 is in the chain, and
     * link2 is an unlinked link
     * @param {Link} link1
     * @param {Link} link2
     */
    linkAfter: function(link1, link2){
        if (this.tailId == link1.id) {
            link1.nextId = link2.id;
            link2.prevId = link1.id;
            this.tailId = link2.id;
        }
        else {
            var nextLink = this.linkHash[link1.nextId];
            link1.nextId = link2.id;
            link2.prevId = link1.id;
            
            if (nextLink !== undefined) {
                link2.nextId = nextLink.id;
                nextLink.prevId = link2.id;
            }
        }
    },
    /**
     * link link1 before link2.  link2 is in the chain
     * and link1 is an unlinked link
     * @param {Link} link1
     * @param {Link} link2
     */
    linkBefore: function(link1, link2){
        if (this.headId == link2.id) {
            link1.nextId = link2.id;
            link2.prevId = link1.id;
            this.headId = link1.id;
        }
        else {
            var prevLink = this.linkHash[link2.prevId];
            link1.nextId = link2.id;
            link2.prevId = link1.id;
            
            if (prevLink !== undefined) {
                prevLink.nextId = link1.id;
                link1.prevId = prevLink.id;
            }
        }
    },
    /**
     * set link indices
     */
    setLinkIndices: function(){
        for (var n = 0; n < this.links.length; n++) {
            this.links[n].index = n;
        }
    }
};
///////////////////////////////////////////////////////////////////////
//  Stage
///////////////////////////////////////////////////////////////////////
/**
 * Stage constructor
 * @param {String} containerId
 * @param {int} width
 * @param {int} height
 */
Kinetic.Stage = function(containerId, width, height){
    this.container = document.getElementById(containerId);
    this.width = width;
    this.height = height;
    this.layerIdCounter = 0;
    this.scale = {
        x: 1,
        y: 1
    };
    this.layerIdCounter = 0;
    this.dblClickWindow = 400;
    this.targetShape = {};
    this.clickStart = false;
    this.layerNames = {};
    
    // desktop flags
    this.mousePos = null;
    this.mouseDown = false;
    this.mouseUp = false;
    
    // mobile flags
    this.touchPos = null;
    this.touchStart = false;
    this.touchEnd = false;
    
    // user defined layers
    this.layers = [];
    
    /*
     * Layer roles
     *
     * buffer - canvas compositing
     * backstage - path detection
     */
    var that = this;
    this.bufferLayer = new Kinetic.Layer();
    this.backstageLayer = new Kinetic.Layer();
    
    // customize back stage context
    var backstageLayer = this.backstageLayer;
    backstageLayer.context.stroke = function(){
    };
    backstageLayer.context.fill = function(){
    };
    backstageLayer.context.fillRect = function(x, y, width, height){
        backstageLayer.context.rect(x, y, width, height);
    };
    backstageLayer.context.strokeRect = function(x, y, width, height){
        that.context.rect(x, y, width, height);
    };
    backstageLayer.context.drawImage = function(){
    };
    backstageLayer.context.fillText = function(){
    };
    backstageLayer.context.strokeText = function(){
    };
    
    this.bufferLayer.getCanvas().style.display = 'none';
    this.backstageLayer.getCanvas().style.display = 'none';
    
    // add buffer layer
    this.bufferLayer.stage = this;
    this.bufferLayer.canvas.width = this.width;
    this.bufferLayer.canvas.height = this.height;
    this.container.appendChild(this.bufferLayer.canvas);
    
    // add backstage layer
    this.backstageLayer.stage = this;
    this.backstageLayer.canvas.width = this.width;
    this.backstageLayer.canvas.height = this.height;
    this.container.appendChild(this.backstageLayer.canvas);
    
    this.listen();
    
    this.on("mouseout", function(evt){
        that.shapeDragging = undefined;
    }, false);
    
    /*
     * prepare drag and drop
     */
    var types = [{
        end: "mouseup",
        move: "mousemove"
    }, {
        end: "touchend",
        move: "touchmove"
    }];
    
    for (var n = 0; n < types.length; n++) {
        var pubType = types[n];
        (function(){
            var type = pubType;
            that.on(type.move, function(evt){
                if (that.shapeDragging) {
                    var pos = type.move == "mousemove" ? that.getMousePosition() : that.getTouchPosition();
                    if (that.shapeDragging.drag.x) {
                        that.shapeDragging.x = pos.x - that.shapeDragging.offset.x;
                    }
                    if (that.shapeDragging.drag.y) {
                        that.shapeDragging.y = pos.y - that.shapeDragging.offset.y;
                    }
                    that.shapeDragging.layer.draw();
                    
                    // execute user defined ondragend if defined
                    Kinetic.GlobalObject.handleEvents(that.shapeDragging, "ondragmove", evt);
                }
            }, false);
            that.on(type.end, function(evt){
                // execute user defined ondragend if defined
                if (that.shapeDragging) {
                    Kinetic.GlobalObject.handleEvents(that.shapeDragging, "ondragend", evt);
                }
                that.shapeDragging = undefined;
            });
        })();
    }
    
    this.on("touchend", function(evt){
        // execute user defined ondragend if defined
        if (that.shapeDragging) {
            Kinetic.GlobalObject.handleEvents(that.shapeDragging, "ondragend", evt);
        }
        that.shapeDragging = undefined;
    });
    
    // add stage to global object
    var stages = Kinetic.GlobalObject.stages;
    stages.push(this);
    // set stage id
    this.id = stages.length - 1;
};

/*
 * Stage methods
 */
Kinetic.Stage.prototype = {
    /**
     * set stage size
     * @param {int} width
     * @param {int} height
     */
    setSize: function(width, height){
        var layers = this.layers;
        for (n = 0; n < layers.length; n++) {
            var layer = layers[n];
            layer.getCanvas().width = width;
            layer.getCanvas().height = height;
            layer.draw();
        }
        
        // set stage dimensions
        this.width = width;
        this.height = height;
        
        // set buffer layer and backstage layer sizes
        this.bufferLayer.getCanvas().width = width;
        this.bufferLayer.getCanvas().height = height;
        this.backstageLayer.getCanvas().width = width;
        this.backstageLayer.getCanvas().height = height;
    },
    /**
     * set stage scale
     * @param {int} scaleX
     * @param {int} scaleY
     */
    setScale: function(scaleX, scaleY){
        var oldScaleX = this.scale.x;
        var oldScaleY = this.scale.y;
        
        if (scaleY) {
            this.scale.x = scaleX;
            this.scale.y = scaleY;
        }
        else {
            this.scale.x = scaleX;
            this.scale.y = scaleX;
        }
        
        /*
         * scale all shape positions
         */
        var layers = this.layers;
        for (var n = 0; n < layers.length; n++) {
            var links = layers[n].links;
            for (var i = 0; i < links.length; i++) {
                var shape = links[i].shape;
                shape.x *= this.scale.x / oldScaleX;
                shape.y *= this.scale.y / oldScaleY;
            }
        }
    },
    /**
     * clear all layers
     */
    clear: function(){
        var layers = this.layers;
        for (var n = 0; n < layers.length; n++) {
            layers[n].clear();
        }
    },
    /**
     * set layer indices
     */
    setLayerIndices: function(){
        for (var n = 0; n < this.layers.length; n++) {
            this.layers[n].index = n;
        }
    },
    /**
     * creates a composite data URL and passes it to a callback
     * @param {function} callback
     */
    toDataURL: function(callback){
        var bufferLayer = this.bufferLayer;
        var bufferContext = bufferLayer.getContext();
        var layers = this.layers;
        
        function addLayer(n){
            var dataURL = layers[n].getCanvas().toDataURL();
            var imageObj = new Image();
            imageObj.onload = function(){
                bufferContext.drawImage(this, 0, 0);
                n++;
                if (n < layers.length) {
                    addLayer(n);
                }
                else {
                    callback(bufferLayer.getCanvas().toDataURL());
                }
            };
            imageObj.src = dataURL;
        }
        
        
        bufferLayer.clear();
        addLayer(0);
    },
    
    /**
     * draw shapes
     */
    draw: function(){
        var layers = this.layers;
        for (var n = 0; n < layers.length; n++) {
            layers[n].draw();
        }
    },
    /**
     * remove layer from stage
     * @param {Layer} layer
     */
    remove: function(layer){
        this.layers.splice(layer.id, 1);
        this.setLayerIndices();
        // remove layer canvas from dom
        this.container.removeChild(layer.canvas);
    },
    /**
     * bind event listener to stage (which is essentially
     * the container DOM)
     * @param {string} type
     * @param {function} handler
     */
    on: function(type, handler){
        this.container.addEventListener(type, handler);
    },
    /**
     * add layer to stage
     * @param {Layer} layer
     */
    add: function(layer){
        if (layer.name) {
            this.layerNames[layer.name] = layer;
        }
        layer.canvas.width = this.width;
        layer.canvas.height = this.height;
        layer.stage = this;
        this.layers.push(layer);
        layer.draw();
        this.container.appendChild(layer.canvas);
        
        layer.id = this.layerIdCounter++;
        layer.index = this.layers.length - 1;
    },
    /**
     * get layer by name
     * @param {string} name
     */
    getLayer: function(name){
        return this.layerNames[name];
    },
    /**
     * handle incoming event
     * @param {Event} evt
     */
    handleEvent: function(evt){
        if (!evt) {
            evt = window.event;
        }
        
        this.setMousePosition(evt);
        this.setTouchPosition(evt);
        
        var backstageLayer = this.backstageLayer;
        var backstageLayerContext = backstageLayer.getContext();
        var that = this;
        
        backstageLayer.clear();
        
        /*
         * loop through layers.  If at any point an event
         * is triggered, n is set to -1 which will break out of the
         * three nested loops
         */
        for (var n = this.layers.length - 1; n >= 0; n--) {
            var layer = this.layers[n];
            if (layer.visible && n >= 0 && layer.isListening) {
                var linkId = layer.tailId;
                
                // propapgate backwards through event links
                while (n >= 0 && linkId !== undefined) {
                    //for (var n = this.getEventShapes().length - 1; n >= 0; n--) {
                    //var pubShape = this.getEventShapes()[n];
                    var link = layer.linkHash[linkId];
                    var pubShape = link.shape;
                    (function(){
                        var shape = pubShape;
                        shape.draw(backstageLayer);
                        var pos = that.getUserPosition();
                        var el = shape.eventListeners;
                        
                        if (shape.visible && pos !== null && backstageLayerContext.isPointInPath(pos.x, pos.y)) {
                            // handle onmousedown
                            if (that.mouseDown) {
                                that.mouseDown = false;
                                that.clickStart = true;
                                Kinetic.GlobalObject.handleEvents(shape, "onmousedown", evt);
                                n = -1;
                            }
                            // handle onmouseup & onclick
                            else if (that.mouseUp) {
                                that.mouseUp = false;
                                Kinetic.GlobalObject.handleEvents(shape, "onmouseup", evt);
                                
                                // detect if click or double click occurred
                                if (that.clickStart) {
                                    Kinetic.GlobalObject.handleEvents(shape, "onclick", evt);
                                    
                                    if (shape.inDoubleClickWindow) {
                                        Kinetic.GlobalObject.handleEvents(shape, "ondblclick", evt);
                                    }
                                    shape.inDoubleClickWindow = true;
                                    setTimeout(function(){
                                        shape.inDoubleClickWindow = false;
                                    }, that.dblClickWindow);
                                }
                                n = -1;
                            }
                            
                            // handle touchstart
                            else if (that.touchStart) {
                                that.touchStart = false;
                                Kinetic.GlobalObject.handleEvents(shape, "touchstart", evt);
                                
                                if (el.ondbltap && shape.inDoubleClickWindow) {
                                    var events = el.ondbltap;
                                    for (var i = 0; i < events.length; i++) {
                                        events[i].handler.apply(shape, [evt]);
                                    }
                                }
                                
                                shape.inDoubleClickWindow = true;
                                
                                setTimeout(function(){
                                    shape.inDoubleClickWindow = false;
                                }, that.dblClickWindow);
                                n = -1;
                            }
                            
                            // handle touchend
                            else if (that.touchEnd) {
                                that.touchEnd = false;
                                Kinetic.GlobalObject.handleEvents(shape, "touchend", evt);
                                n = -1;
                            }
                            
                            // handle touchmove
                            else if (el.touchmove) {
                                Kinetic.GlobalObject.handleEvents(shape, "touchmove", evt);
                                n = -1;
                            }
                            
                            /*
                             * this condition is used to identify a new target shape.
                             * A new target shape occurs if a target shape is not defined or
                             * if the current shape is different from the current target shape and
                             * the current shape is beneath the target
                             */
                            else if (that.targetShape.id === undefined || (that.targetShape.id != shape.id && that.targetShape.getZIndex() < shape.getZIndex())) {
                                /*
                                 * check if old target has an onmouseout event listener
                                 */
                                var oldEl = that.targetShape.eventListeners;
                                if (oldEl && oldEl.onmouseout) {
                                    Kinetic.GlobalObject.handleEvents(that.targetShape, "onmouseout", evt);
                                }
                                
                                // set new target shape
                                that.targetShape = shape;
                                
                                // handle onmouseover
                                Kinetic.GlobalObject.handleEvents(shape, "onmouseover", evt);
                                n = -1;
                            }
                            
                            // handle onmousemove
                            else if (el.onmousemove) {
                                Kinetic.GlobalObject.handleEvents(shape, "onmousemove", evt);
                                n = -1;
                            }
                        }
                        // handle mouseout condition
                        else if (that.targetShape.id == shape.id) {
                            that.targetShape = {};
                            Kinetic.GlobalObject.handleEvents(shape, "onmouseout", evt);
                            n = -1;
                        }
                    }());
                    
                    linkId = link.prevId;
                } // end links loop
            }
        } // end layer loop
    },
    /**
     * begin listening for events by adding event handlers
     * to the container
     */
    listen: function(){
        var that = this;
        
        // desktop events
        this.container.addEventListener("mousedown", function(evt){
            that.mouseDown = true;
            that.handleEvent(evt);
        }, false);
        
        this.container.addEventListener("mousemove", function(evt){
            that.mouseUp = false;
            that.mouseDown = false;
            that.handleEvent(evt);
        }, false);
        
        this.container.addEventListener("mouseup", function(evt){
            that.mouseUp = true;
            that.mouseDown = false;
            that.handleEvent(evt);
            
            that.clickStart = false;
        }, false);
        
        this.container.addEventListener("mouseover", function(evt){
            that.handleEvent(evt);
        }, false);
        
        this.container.addEventListener("mouseout", function(evt){
            that.mousePos = null;
        }, false);
        // mobile events
        this.container.addEventListener("touchstart", function(evt){
            evt.preventDefault();
            that.touchStart = true;
            that.handleEvent(evt);
        }, false);
        
        this.container.addEventListener("touchmove", function(evt){
            evt.preventDefault();
            that.handleEvent(evt);
        }, false);
        
        this.container.addEventListener("touchend", function(evt){
            evt.preventDefault();
            that.touchEnd = true;
            that.handleEvent(evt);
        }, false);
    },
    /**
     * get mouse position for desktop apps
     * @param {Event} evt
     */
    getMousePosition: function(evt){
        return this.mousePos;
    },
    /**
     * get touch position for mobile apps
     * @param {Event} evt
     */
    getTouchPosition: function(evt){
        return this.touchPos;
    },
    /**
     * get user position (mouse position or touch position)
     * @param {Event} evt
     */
    getUserPosition: function(evt){
        return this.getTouchPosition() || this.getMousePosition();
    },
    /**
     * set mouse positon for desktop apps
     * @param {Event} evt
     */
    setMousePosition: function(evt){
        var mouseX = evt.clientX - this.getContainerPosition().left + window.pageXOffset;
        var mouseY = evt.clientY - this.getContainerPosition().top + window.pageYOffset;
        this.mousePos = {
            x: mouseX,
            y: mouseY
        };
    },
    /**
     * set touch position for mobile apps
     * @param {Event} evt
     */
    setTouchPosition: function(evt){
        if (evt.touches !== undefined && evt.touches.length == 1) {// Only deal with
            // one finger
            var touch = evt.touches[0];
            // Get the information for finger #1
            var touchX = touch.clientX - this.getContainerPosition().left + window.pageXOffset;
            var touchY = touch.clientY - this.getContainerPosition().top + window.pageYOffset;
            
            this.touchPos = {
                x: touchX,
                y: touchY
            };
        }
    },
    /**
     * get container position
     */
    getContainerPosition: function(){
        var obj = this.container;
        var top = 0;
        var left = 0;
        while (obj && obj.tagName != "BODY") {
            top += obj.offsetTop;
            left += obj.offsetLeft;
            obj = obj.offsetParent;
        }
        return {
            top: top,
            left: left
        };
    },
    /**
     * get container DOM element
     */
    getContainer: function(){
        return this.container;
    }
};

///////////////////////////////////////////////////////////////////////
//  Shape
///////////////////////////////////////////////////////////////////////
/**
 * Shape constructor
 * @param {function} drawFunc
 * @param {string} name
 */
Kinetic.Shape = function(drawFunc, name){
    this.isListening = true;
    this.drawFunc = drawFunc;
    this.name = name;
    this.x = 0;
    this.y = 0;
    this.scale = {
        x: 1,
        y: 1
    };
    this.rotation = 0;
    // radians
    // store state for next clear
    this.lastX = 0;
    this.lastY = 0;
    this.lastRotation = 0;
    // radians
    this.lastScale = {
        x: 1,
        y: 1
    };
    
    this.eventListeners = {};
    this.visible = true;
    this.drag = {
        x: false,
        y: false
    };
};
/*
 * Shape emthods
 */
Kinetic.Shape.prototype = {
    /**
     * Listen or don't listen to layer events
     * @param {boolean} isListening
     */
    listen: function(isListening){
        // if shape is in layer
        if (this.link) {
            // if changing isListening
            if (isListening != this.isListening) {
                // is now listening
                if (isListening) {
                    //TODO
                }
                // if now not listening
                else {
                    //TODO
                }
            }
        }
        
        this.isListening = isListening;
    },
    /**
     * get shape temp layer context
     */
    getContext: function(){
        return this.tempLayer.getContext();
    },
    /**
     * get shape temp layer canvas
     */
    getCanvas: function(){
        return this.tempLayer.getCanvas();
    },
    /**
     * get stage
     */
    getStage: function(){
        return this.layer.stage;
    },
    /**
     * draw shape
     * @param {Layer} layer
     */
    draw: function(layer){
        if (this.visible) {
            //var layer = this.layer;
            var stage = layer.stage;
            var context = layer.getContext();
            
            // shape transform
            context.save();
            if (this.x !== 0 || this.y !== 0) {
                context.translate(this.x, this.y);
            }
            if (this.rotation !== 0) {
                context.rotate(this.rotation);
            }
            if (this.scale.x != 1 || this.scale.y != 1) {
                context.scale(this.scale.x, this.scale.y);
            }
            
            // layer transform
            context.save();
            if (stage.scale.x != 1 || stage.scale.y != 1) {
                context.scale(stage.scale.x, stage.scale.y);
            }
            
            this.tempLayer = layer;
            this.drawFunc.call(this);
            
            context.restore();
            context.restore();
        }
    },
    /**
     * initialize drag and drop
     */
    initDrag: function(){
        var that = this;
        var types = ["mousedown", "touchstart"];
        
        for (var n = 0; n < types.length; n++) {
            var pubType = types[n];
            (function(){
                var type = pubType;
                that.on(type + ".initdrag", function(evt){
                    var stage = that.layer.stage;
                    var pos = stage.getUserPosition();
                    
                    if (pos) {
                        stage.shapeDragging = that;
                        stage.shapeDragging.offset = {};
                        stage.shapeDragging.offset.x = pos.x - that.x;
                        stage.shapeDragging.offset.y = pos.y - that.y;
                        
                        // execute dragstart events if defined
                        Kinetic.GlobalObject.handleEvents(that, "ondragstart", evt);
                    }
                });
            })();
        }
    },
    /**
     * remove drag and drop event listener
     */
    dragCleanup: function(){
        if (!this.drag.x && !this.drag.y) {
            this.off("mousedown.initdrag");
            this.off("touchstart.initdrag");
        }
    },
    /**
     * enable/disable drag and drop for box x and y direction
     * @param {boolean} setDraggable
     */
    draggable: function(setDraggable){
        if (setDraggable) {
            var needInit = !this.drag.x && !this.drag.y;
            this.drag = {
                x: true,
                y: true
            };
            if (needInit) {
                this.initDrag();
            }
        }
        else {
            this.drag = {
                x: false,
                y: false
            };
            this.dragCleanup();
        }
    },
    /**
     * enable/disable drag and drop for x only
     * @param {boolean} setDraggable
     */
    draggableX: function(setDraggable){
        if (setDraggable) {
            var needInit = !this.drag.x && !this.drag.y;
            this.drag.x = true;
            if (needInit) {
                this.initDrag();
            }
        }
        else {
            this.drag.x = false;
            this.dragCleanup();
        }
    },
    /**
     * enable/disable drag and drop for y only
     * @param {boolean} setDraggable
     */
    draggableY: function(setDraggable){
        if (setDraggable) {
            var needInit = !this.drag.x && !this.drag.y;
            this.drag.y = true;
            if (needInit) {
                this.initDrag();
            }
        }
        else {
            this.drag.y = false;
            this.dragCleanup();
        }
    },
    /**
     * get zIndex
     */
    getZIndex: function(){
        return this.link.index;
    },
    /**
     * set shape scale
     * @param {number} scaleX
     * @param {number} scaleY
     */
    setScale: function(scaleX, scaleY){
        if (scaleY) {
            this.scale.x = scaleX;
            this.scale.y = scaleY;
        }
        else {
            this.scale.x = scaleX;
            this.scale.y = scaleX;
        }
    },
    /**
     * set shape position
     * @param {number} x
     * @param {number} y
     */
    setPosition: function(x, y){
        this.x = x;
        this.y = y;
    },
    /**
     * get shape position
     */
    getPosition: function(){
        return {
            x: this.x,
            y: this.y
        };
    },
    /**
     * move shape
     * @param {number} x
     * @param {number} y
     */
    move: function(x, y){
        this.x += x;
        this.y += y;
    },
    /**
     * set shape rotation
     * @param {number} theta
     */
    setRotation: function(theta){
        this.rotation = theta;
    },
    /**
     * rotate shape
     * @param {number} theta
     */
    rotate: function(theta){
        this.rotation += theta;
    },
    /**
     * bind event listener to shape
     * @param {string} typesStr
     * @param {function} handler
     */
    on: function(typesStr, handler){
        Kinetic.GlobalObject.bind(this.eventListeners, typesStr, handler);
    },
    /**
     * remove event listener from shape
     * @param {string} type
     */
    off: function(typesStr){
        Kinetic.GlobalObject.unbind(this.eventListeners, typesStr);
    },
    /**
     * show shape
     */
    show: function(){
        this.visible = true;
    },
    /**
     * hide shape
     */
    hide: function(){
        this.visible = false;
    },
    /**
     * move shape to top
     */
    moveToTop: function(){
        var link = this.link;
        var index = link.index;
        var layer = this.layer;
        this.layer.links.splice(index, 1);
        this.layer.links.push(link);
        layer.setLinkIndices();
        
        
        // alter link structure if more than one event link in the layer
        if (link.nextId !== undefined || link.prevId !== undefined) {
            layer.unlink(link);
            var tailLink = layer.linkHash[layer.tailId];
            layer.linkAfter(tailLink, link);
        }
    },
    /**
     * move shape up
     */
    moveUp: function(){
        var link = this.link;
        var index = link.index;
        var layer = this.layer;
        var nextLink = layer.linkHash[link.nextId];
        
        // only do something if there's a link above
        if (nextLink) {
            // swap links
            this.layer.links.splice(index, 1);
            this.layer.links.splice(index + 1, 0, link);
            layer.setLinkIndices();
            
            layer.unlink(link);
            layer.linkAfter(nextLink, link);
        }
    },
    /**
     * move shape down
     */
    moveDown: function(){
        var link = this.link;
        var index = link.index;
        var layer = this.layer;
        var prevLink = layer.linkHash[link.prevId];
        
        // only do something if there's a link above
        if (prevLink) {
            // swap links
            this.layer.links.splice(index, 1);
            this.layer.links.splice(index - 1, 0, link);
            layer.setLinkIndices();
            
            layer.unlink(link);
            layer.linkBefore(link, prevLink);
        }
    },
    /**
     * move shape to bottom
     */
    moveToBottom: function(){
        var link = this.link;
        var index = link.index;
        var layer = this.layer;
        this.layer.links.splice(index, 1);
        this.layer.links.unshift(link);
        
        layer.setLinkIndices();
        
        // alter link structure if more than one link in the layer
        if (link.nextId !== undefined || link.prevId !== undefined) {
            layer.unlink(link);
            var head = layer.linkHash[layer.headId];
            layer.linkBefore(link, head);
        }
    },
    /**
     * set zIndex
     * @param {int} index
     */
    setZIndex: function(zIndex){
        var link = this.link;
        var index = link.index;
        var layer = this.layer;
        // get link currently at specified index
        var curLink = layer.linkHash[zIndex];
        
        if (curLink !== undefined) {
            layer.links.splice(index, 1);
            layer.links.splice(zIndex, 0, link);
            layer.setLinkIndices();
            
            layer.unlink(link);
            layer.linkAfter(curLink, link);
        }
    },
    /**
     * get shape's layer
     */
    getLayer: function(){
        return this.layer;
    },
    /**
     * move shape to another layer
     * @param {Layer} newLayer
     */
    moveToLayer: function(newLayer){
        var layer = this.layer;
        var link = this.link;
        layer.unlink(link);
        layer.removeLink(link);
        newLayer.addLink(link);
    }
};
