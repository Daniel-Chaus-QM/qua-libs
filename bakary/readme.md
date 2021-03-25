# Waveform baking
This library introduces a new framework for creating arbitrary waveforms and storing them in a usual configuration file. 
The idea is to simplify the writing of pulse samples that would usually be declared as incompatible with respect to QUA restrictions for uploading the samples to the OPX. A nice advantage of using this tool is to embed into one single waveform a series of instructions that allows program memory preservation.

Waveform baking is embedded into a new context manager, declared prior to the QUA program, that takes two inputs : 

- the configuration dictionary (the same used to initialize a Quantum Machine instance),

- a padding method : to be chosen between : “right”, “left”, “symmetric_l”, “symmetric_r”.  This string indicates how should the samples be filled up with 0s when they do not correspond to a usual sample (that is if sample length is not a multiple of 4 or if it is shorter than 16 ns). 

    -  “right” setting is the default setting and pads 0s at the end of the baked sample to insert a QUA compatible version in the original configuration file

    - “left” pads 0s before the baked sample

    - “symmetric_l” pads 0s symmetrically before and after the baked sample, putting one more 0 before it in case the baked sample length is odd

    - “symmetric_r' pads 0s symmetrically before and after the baked sample , putting one more 0 after it in case the baked sample length is odd

Declaration is done before the QUA program as follows : 

```
with baking(config, padding_method = "symmetric_r") as b:
  b.align("qe1", "qe2", "qe3")
  b.frame_rotation(0.78, "qe2")
  b.ramp(amp=0.3, duration=9, qe="qe1")
```

This context manager does not return any output, its execution results in an edition of the configuration file provided as input to add an operation to all quantum elements involved in the commands inserted in the baking, an associated pulse, and finally an associated waveform that contains the operations indicated in the context manager, and has the property of being appropriately sorted such that a QUA program can execute such sample in one play command, instead of having to run different commands that would not correspond to the criteria mentioned above for sample length.  The baking also carries advantages for an efficient program memory management, in the sense that there are less commands and different samples to be stored in memory to execute the program.

# **How can I add operations inside the baking context manager?**

The logic behind the baking context manager is to stay as close as possible to the way we would write play statements within a QUA program. For instance, commands like frame_rotation, reset_phase, ramp, wait and align are all replicated  within the context manager. 

For playing custom operations, from an arbitrary shaped waveform the procedure goes as follows:

1. You first have to write down the sample you want to use as a waveform (with arbitrary length, no matter if it does not match usual QUA criteria for saving a waveform in memory ) in the form of a Python list.
    - If the sample is meant for a singleInput element, the list should contain the sample itself. 
    - Contrariwise, if it is intended for a mixInputs element, the list should contain two Python lists as [sample_I, sample_Q], where sample_I and sample_Q are themselves Python lists containing the samples.

2. Add the sample to the local configuration, with method **add_Op**, which takes 4 inputs : 
    - the name of the operation (name you will use only within the baking context manager in a play statement)
    - the quantum element for which you want to add the operation
    - the samples to store as waveforms
    - the digital_marker name (supposedly already existing in the configuration) to attach to the pulse associated to the operation.

3. Use a baking **play** statement, specifying the operation name (which should correspond to the name introduced in the add_Op method) and the quantum element to play the operation on

All those commands concatenated altogether eventually build one single “big” waveform per quantum element involved in the baking that contains all the instructions specified in the baking environment. The exiting procedure of the baking ensures that the appropriate padding is done to ensure that QUA will be able to play this arbitrary waveform.

Here is a code example : 


```
with baking(config, padding_method = "symmetric_r") as b:

# Create arbitrary waveforms 

  singleInput_sample = [1., 0.8, 0.6, 0.8, 0.9]
  mixInput_sample_I = [1.2, 0.3, 0.5]
  mixInput_sample_Q = [0.8, 0.2, 0.4]
  
  # Assign waveforms to quantum element operation
  
  b.add_Op("single_Input_Op", "qe1", singleInput_sample, digital_marker= None)
  b.add_Op("mix_Input_Op", "qe2", [mixInput_sample_I, mixInput_sample_Q], digital_marker = None)
  
  # Play the operations
  
  b.play("single_Input_Op", "qe1")
  b.play("mix_Input_Op", "qe2")
```
# **How to play in QUA my baked waveforms?**

The baking object has a method called run, which takes no inputs and simply does appropriate alignment between quantum elements involved in the baking and play simultaneously (using this time a QUA play statement) the previously baked waveforms. Therefore, what is left to do is to **call the run method associated to the baking object within the actual QUA program**.

```
with baking(config, "left"):
  #Create your baked waveform, cf snippet above
  
#Open QUA program : 
with program() as QUA_prog:
  b.run()
```
# **Additional features of the baking environment**

The baking aims to be as versatile as possible in the way of editing samples. The idea is therefore to generate desired samples up to the precision of the nanosecond, without having to worry about its format and its insertion in the configuration file. It is even possible to generate a sample based on two previous samples (like a pulse superposition) by using two commands introduced in the baking : **play_at()** and **negative wait**.

Let’s take a look at the code below to understand what these two features do : 

```
with baking(config=config, padding_method="symmetric_r") as b:
    const_Op = [0.3, 0.3, 0.3, 0.3, 0.3]
    const_Op2 = [0.2, 0.2, 0.2, 0.3, 0.4]
    b.add_Op("Op1", "qe1", [const_Op, const_Op2]) # qe1 is a mixInputs element
    Op3 = [1., 1., 1.]
    Op4 = [2., 2., 2.]
    b.add_Op("Op2", "qe1", [Op3, Op4])
    b.play("Op1", "qe1")   
    
    # The baked waveform is at this point I : [0.3, 0.3, 0.3, 0.3, 0.3]
    #                                     Q : [0.2, 0.2, 0.2, 0.3, 0.4]
    
    b.play_at("Op3", "qe1", t=2)
    #t indicates the time index where this new sample should be added
    # The baked waveform is now I : [0.3, 0.3, 1.3, 1.3, 1.3]
    #                                     Q : [0.2, 0.2, 2.2, 2.3, 2.4]
    
"""At the baking exit, the config will have an updated sample 
adapted for QUA compilation, according to the padding_method chosen, in this case:
I : [0, 0, 0, 0, 0, 0.3, 0.3, 1.3, 1.3, 1.3, 0, 0, 0, 0, 0, 0], 
Q: [0, 0, 0, 0, 0, 0.2, 0.2, 2.2, 2.3, 2.4, 0, 0, 0, 0, 0, 0]
```
If the time index t is positive, the sample will be added precisely at the index indicated in the existing sample.
Contrariwise, if the provided index t is negative, we call here automatically the function **negative_wait**, which adds the sample at the provided index starting to count from the end of the existing sample : 
```
with baking(config=config, padding_method="symmetric_r") as b:
    const_Op = [0.3, 0.3, 0.3, 0.3, 0.3]
    const_Op2 = [0.2, 0.2, 0.2, 0.3, 0.4]
    b.add_Op("Op1", "qe1", [const_Op, const_Op2]) #qe1 is a mixInputs element
    Op3 = [1., 1., 1.]
    Op4 = [2., 2., 2.]
    b.add_Op("Op2", "qe1", [Op3, Op4])
    b.play("Op1", "qe1")   
    # The baked waveform is at this point I : [0.3, 0.3, 0.3, 0.3, 0.3]
    #                                     Q : [0.2, 0.2, 0.2, 0.3, 0.4]
    b.play_at("Op3", "qe1", t=-2) #t indicates the time index where this new sample should be added
    # The baked waveform is now I : [0.3, 0.3, 0.3, 1.3, 1.3, 1.0]
    #                                     Q : [0.2, 0.2, 0.2, 2.3, 2.4, 2.0]
    
""" At the baking exit, the config will have an updated sample 
adapted for QUA compilation, according to the padding_method chosen, in this case: """
I : [0, 0, 0, 0, 0, 0.3, 0.3, 0.3, 1.3, 1.3, 1.0, 0, 0, 0, 0, 0], 
Q:  [0, 0, 0, 0, 0, 0.2, 0.2, 0.2, 2.3, 2.4, 2.0, 0, 0, 0, 0, 0]
```
The **play_at** command can also be used as a single play statement involving a wait time and a play statement. In fact, if the time index indicated in the function is actually out of the range of the existing sample, a wait command is automatically added until reaching this time index (recall that the index corresponds to the time in ns) and starts inserting the operation indicated at this time. See the example below : 

```
with baking(config=config, padding_method="symmetric_r") as b:
    const_Op = [0.3, 0.3, 0.3, 0.3, 0.3]
    const_Op2 = [0.2, 0.2, 0.2, 0.3, 0.4]
    b.add_Op("Op1", "qe1", [const_Op, const_Op2]) #qe1 is a mixInputs element
    Op3 = [1., 1., 1.]
    Op4 = [2., 2., 2.]
    b.add_Op("Op2", "qe1", [Op3, Op4])
    b.play("Op1", "qe1")   
    # The baked waveform is at this point I : [0.3, 0.3, 0.3, 0.3, 0.3]
    #                                     Q : [0.2, 0.2, 0.2, 0.3, 0.4]
    b.play_at("Op3", "qe1", t=8) #t indicates the time index where this new sample should be added
    # The baked waveform is now 
    # I : [0.3, 0.3, 0.3, 0.3, 0.3, 0, 0, 0, 1.0, 1.0, 1.0], 
    # Q : [0.2, 0.2, 0.2, 0.3, 0.4, 0, 0, 0, 2.0, 2.0, 2.0]}
    #                                    
    
"""At the baking exit, the config will have an updated sample 
adapted for QUA compilation, according to the padding_method chosen, in this case:
I : [0.3, 0.3, 0.3, 0.3, 0.3, 0, 0, 0, 1.0, 1.0, 1.0, 0, 0, 0, 0, 0], 
Q : [0.2, 0.2, 0.2, 0.3, 0.4, 0, 0, 0, 2.0, 2.0, 2.0, 0, 0, 0, 0, 0]
"""
```

# The negative wait

Negative wait is at the moment, just an equivalent way of writing the play_at statement.

The idea is to move backwards the time index at which the following play statement should start (wait[-3] means that the following waveform will be added on top of the existing sequence on the 3 last samples and will append the rest like a usual play statement.

We have the equivalence between:
```
b.wait(-3)
b.play('my_pulse',qe)
```
and 
```
b.play_at('my_pulse', qe, t=-3)
```


