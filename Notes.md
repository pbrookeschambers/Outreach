
## Equipment

 - iPads + IR cameras
 - Fancier IR cameras
 - Spectrometers for iPads
    - Currently, the probe uses a single fibre-optic, so the aperture is impractically small
    - Could try modifying to add a mirror and do away with the fibre-optic
 - Speaker System
    - Currently only used by Chris for outreach with blind and partially sighted people for an accessible planetarium show
    - Could be used for other outreach events
 - Giant roll of black paper
    - Scale of the universe
        - If we can find a way to fold it well, we could also demonstrate expansion?
    - Scale of atoms etc?
 - Programmable Light Stick
    - Individually addressable LEDS with controller
    - Long exposure photography
    - Could show something to do with how graphs are made up of individual points?
        - Possibly some way to visually show differentiation/integration?
        - Something to do with how integration (area) is the same as summation (sort of)?
 - Solar Telescope
 - Tesla Coil (does **not** leave the university) 
 - Ultrasound kit
    - Originally intended for Stage 1 projects, but never used
 - Theremin

## Previous Activities

 - Planet Making
    - Fill and decorate balloons with rice for a rocky planet or fibre for a gas giant
    - Decorate with paint, glue, etc.
    - Usually for KS2
 - Bottle Rockets
    - Currently not that great
    - Just uses the bottle as an air chamber, squashed to launch a paper rocket
 - Crater Activity:
    - Uses a tray of flour, cocoa powder, etc. to simulate a planet surface
    - Use the ballistics launcher to fire a ball bearing into the surface
    - Shows that the crater is almost always round, unless it's at a really steep angle
    - Shows that sub-surface material is thrown out of the crater
        - Link to moon craters and ejected material
 - Cloud Chambers
    - Really good on site, but too large to transport currently
    - Could be miniaturised using food containers instead. Transporting dry ice not too much of a problem.
 - Projectiles
    - As done for enrichment events, good for A-Level students. 
 - Physics escape rooms
    - Already very good, don't really need any adjustments
 - Mars Rover
    - Students select (3D printed) parts based on a goal and a budget in teams, and assemble into a rover.


## Ideas

 - We have very little to do with:
    - Forces
    - Circuits
    - Robotics etc

 - A few music/sound themed activities would be good
    - Visualising standing waves with Ruben's Tube? (More of a demonstration than an activity)
    - 2D standing waves with a vibrating plate and sand?
    - Slapaphone
        - Have to work out which pipes would make a given note, construct a pipe instrument, then play something as a group (in the hall of the mountain king, ode to joy etc., something simple)
        - (apparently) $l = r + \frac{v}{2f}$ where $l$ is the length of the pipe, $r$ the internal radius, $v$ the speed of sound in air, and $f$ the desired frequency
    - Membrane wind instrument out of PVC piping
        - Different membranes
    - Improvised oscilloscope
        - Mirror on a stretched membrane (balloon)
        - Laser pointer
        - For best results, glow in the dark paint on the target screen

- Light
    - Long-exposure and IR themed things lend themselves well to astro themed activities.
    - Some stuff to do with refraction could be fun?
    - Water droplet microscope
        - Very simple equipment
        - Somewhat fiddly to get right
        - Can be pretty impressive with e.g. pond water
    - Making a pinhole camera
        - Can talk about diffraction, resolution, etc.
    - Spectroscopy
        - Flame tests for identifying elements by spectral lines as well as just colour
    - Refraction of a laser to measure concentration of (e.g.) sugar in water?
    - Holographic chocolate
        - *Tempered* chocolate (important) on a diffraction grating produces a holographic image
        - Can (if done well) produce a 3D image, even in colour
        - Can do small moulds straight from the holographic foil, or larger ones with silicone moulds


- Circuits
    - Conductive pens
    - "Spintronics" mechanical circuit analogue
    - Can do a *lot* with a pi/arduino with a voltmeter, e.g.:
        - Have to get a specific voltage/current with a given set of resistors by working out what to have in series and parallel
            - Could be a fun addition to one of the escape rooms, as a sort of combination lock?
    - Binary counter? Possibly too complicated and/or a bit dry
    - DIY Scalextric somehow?

- 2D acrylic cross-sections of weird fluid dynamics, Steve Mould-style
    - More demonstration than activity, but could be done as an activity if we can find a reliable way for them to easily make the `tracks`. Plasticine, maybe?
    - Maze-solving water (might not be reliable)
    - Heron's fountain
    - Greedy cup
    - Gluggle jug
    - Magnetic strips for sealing?

- Programming
    - Programmable car 
        - Arduino powered
        - Either use actual Arduino code or a block-based language (Would need to be custom?)
        - With an LED board, could be used to show pathfinding algorithms?
        - Snake-like game? Maze solving?
        - Would need to be:
            - Several small groups
            - One or two cars
            - Some sort of simulation to test their code before running it on the car
            - Some sort of scoring system?
            - Some pre-made games to solve
    - Some web-based simulation stuff, would require no equipment

- Rubber band powered vehicles (potential and kinetic energy):
    - car (duh)
    - boat - propeller vs paddle wheel etc
    - helicopter-like thing
        - Da Vinci's original flying machine
        - Why is it unstable? Can we fix it? etc

- Bottle Rockets
    - Several ways to do this

- Levitating spinning top
    - Apparently quite fiddly to get right

- Rubber membrane gravity well
    - Rubber membrane stretched over a frame
    - Place a ball bearing on the membrane
    - Stretch the membrane down to create a gravity well
    - Could be used to demonstrate orbits, escape velocity, etc.

- Electroplating organic material?
    - Use the silver mirror reaction to coat anything in silver
    - Now use that as a conductive surface for electroplating
    - Could give this a physics spin, but realistically this is chemistry

## Activity Packs

- Should have:
    - Title page:
        - Name
        - Description
        - Age range
        - Time required
        - "Works well with" other activities
        - For on campus only
    - Frontmatter:
        - Relevant curriculum links for each exam board
        - Pre-requisites
        - Safety considerations
        - Equipment required (table, laminate with number out and number in columns for dry-wipe pens, etc.)
    - Instructions
        - Instructions for the activity leader
            - Safety considerations at the relevant points (repeated from frontmatter)
            - Clearly marked adjustments for different age ranges
            - Potential pitfalls
        - Instructions for the students
            - Safety considerations at the relevant points
    - Additional talking points
        - Things that are not necessarily part of the activity, but are interesting and relevant
    - Worksheets/Handouts
        - For the students to fill in
        - Answers for the activity leader
            - Possible hints for the students if they get stuck
        - Digital versions as well?
    - Risk Assessment


## LaTeX

 - 4 packages:
    - NUOutreach
        - Contains commands and info common to all the documents to be produced
    - NUCover
        - Handles creating and formatting the cover page and the frontmatter
            - Title
            - Description 
            - Duration
            - Age range
            - Curriculum links
            - Prerequisites
            - Equipment required
                - With a checklist
            - Safety considerations
                - This can still be taken from the instructions, it'll just need a tiny bit of re-working
    - NUInstructions
        - Handles creating the instructions for the activity leader and the students as two separate files
        - Use a flag set in an aux file to determine which to compile
            - This way we can easily use a makefile or similar to compile both at once
    - NUWorksheet
        - Handles creating the worksheets and handouts for the students, and a version with sample answers for the activity leader
        - Again, use a flag set in an aux file to determine which to compile

### File Structure

- Each activity should have its own directory, with three files inside:
    - `cover.tex`
    - `instructions.tex`
    - `worksheet.tex`