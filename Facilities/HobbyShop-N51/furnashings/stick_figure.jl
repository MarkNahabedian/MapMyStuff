using ShaperOriginDesignLib

struct Human
    head_diameter
    neck_length
    spine_length
    limb_length
end

function draw(h::Human)
    llxy = h.limb_length / sqrt(2)
    pathd([ "M", 0, 0 ],
          [ "m", 0, h.head_diameter ],

          [ "a", h.head_diameter/2, h.head_diameter/2,
            0, 1, 0,
            0, - h.head_diameter ],
          [ "a", h.head_diameter/2, h.head_diameter/2,
            0, 1, 0,
            0, h.head_diameter ],
          
          [ "v", h.neck_length ],
          [ "h", h.limb_length ],
          [ "m", - h.limb_length, 0 ],
          [ "h", - h.limb_length ],
          [ "m", h.limb_length, 0 ],
          
          [ "v", h.spine_length ],
          [ "l", llxy, llxy ],
          [ "m", - llxy, - llxy ],
          [ "l", - llxy, llxy ]
          )
end

# draw(Human(1, 0.3, 1.2, 1))


struct Dog
    head_rx
    head_ry
    neck_length
    limb_length
    spine_length
    tail_length
end

function draw(d::Dog)
    neck_xy = d.neck_length / sqrt(2)
    leg_xy = d.limb_length /sqrt(2)
    pathd([ "M", 0, 0 ],
          [ "m", 0, 2 * d.head_rx ],
          [ "a", d.head_rx, d.head_ry,
            0, 1, 0,
            2 * d.head_rx, 0 ],
          [ "a", d.head_rx, d.head_ry,
            0, 1, 0,
            - 2 * d.head_rx, 0 ],
          [ "l", - neck_xy, neck_xy ],
          [ "l", leg_xy, leg_xy ],
          [ "m", - leg_xy, - leg_xy ],
          [ "l", - leg_xy, leg_xy ],
          [ "m", leg_xy, - leg_xy ],
          [ "h", - d.spine_length ],
          [ "l", leg_xy, leg_xy ],
          [ "m", - leg_xy, - leg_xy ],
          [ "l", - leg_xy, leg_xy ],
          [ "m", leg_xy, - leg_xy ],
          [ "v", - d.tail_length ]
          )    
end

# draw(Dog(0.75, 0.3, 0.5, 1.5, 2, 0.5))

