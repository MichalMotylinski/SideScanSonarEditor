---
title: '`SideScanSonarEditor`: A Python package for annotation of side-scan sonar data'
tags:
  - Python package
  - annotation
  - side-scan sonar
  - xtf
authors:
  - name: Michal Motylinski
    orcid: 0000-0002-4764-7130
    equal-contrib: false
    corresponding: true
    affiliation: 1
  - name: Andrew J. Plater
    orcid: 0000-0001-7043-227X
    equal-contrib: false
    affiliation: 1
  - name: Jonathan E. Higham
    orcid: 0000-0001-7577-0913
    equal-contrib: false
    affiliation: 1
affiliations:
 - name: Department of Geography and Planning, School of Environmental Sciences, University of Liverpool, Liverpool, UK
   index: 1

date: 26 February 2025
bibliography: bibliography.bib
---

# Summary

Side-scan sonars are widely used instruments for high-resolution mapping of the seafloor, utilizing acoustic signals to generate detailed imagery. These systems play a crucial role in marine research, habitat assessment, underwater archaeology, and infrastructure inspections, providing valuable insights into seabed features and composition.

Annotation of the targets is typically done using specialised software which does not produce results allowing for quick conversion to formats commonly used to train machine learning models.
Our software `SideScanSonarEditor` is a free and open-source Python package which allows the user to read sonar data from XTF files, display it as images and allow further processing [@xtf:2025].
The key features include the ability to fully analyze sonar imagery, easily manipulate it, and annotate objects of interest.
The tool additionally allows for drawing of polygon shapes as well as rectangular shapes which coordinates are used to crop smaller image tiles. Together they can be used in the process of dataset creation for further sonar analysis or computer vision tasks such as object detection or segmentation.
(\autoref{fig:overview}).

`SideScanSonarEditor` provides the following sonar image manipulation methods:

 - Decimation – across-track down sampling which might be useful when importing very large files that might exceed memory limits on some systems. The decimation factor directly determines the fraction of the data that is to be retained meaning with a factor of 1, 100% of the samples are loaded, with a factor of 2, 50%, factor of 3, 33% and so on. The setting range goes from 1-10 but in reality, values greater than 4 will produce errors or severely reduce the number of samples leading to the loss of a significant portion of data. For the purpose of this research, decimation is set to 1 at all times to ensure the highest number of horizontal features per target.

 - Stretch – Along-track stretch factor which defines how many times each ping should be repeated. This method is applied to improve the visual representation of the features. Typically, when the data is displayed, the objects will appear stretched horizontally and compressed vertically. To compensate without losing across-track features the image is expanded vertically allowing for easier analysis and labelling of the targets. The stretching method, however, is not utilised when generating training data or during inference. The technique is used purely as a visual correction during the annotation process.

 - Invert – Inversion of the colour palette which in some cases might help in visual recognition of targets.

 - Colour mapping – Setting colour palette to highlight different features. Applying different mapping scales can help distinguish various targets on the image. Currently available options include two greyscale patterns a linear (grey) and logarithmic (greylog).

 - Map range – Minimum and maximum mapping ranges are by default automatically calculated based on the intensity input data. Both can be manually modified to change the representation of the features for easier interpretation.

 - Slant range correction - apply slant range correction to compensate for the geometric distortion of the return signal. The corrected image represents true seafloor distances allowing for better alignment with the navigation data [@chang:2010].

![SideScanSonarEditor app \label{fig:overview}](overview.png)

# Statement of Need

Side-scan sonar is a commonly used instrument for mapping of the seabed. These devices operate by being towed behind a vessel, emitting sonar pulses that reflect off the seabed to create detailed images. The raw data collected by the sonar consists of overlapping representations of the seabed that must be processed before they can be used for machine learning applications, such as target recognition and labeling [@Motylinski:2025].

Interpreting side-scan sonar data from sonar typically requires expensive proprietary software designed for in-depth analysis and post-processing. However, these software packages do not facilitate the extraction of imagery and annotations in a format suitable for training computer vision models or further processing [@lin:2014]. To train an automatic target recognition model, users must manually crop imagery in `SonarWiz` (or similar closed-source software) before annotating it using `LabelMe` or other standard tools [@wada:2024]. This process is highly time-consuming, requiring manual visual analysis of sonar swaths in `SonarWiz` or `EdgeTech Discover` to identify and crop relevant areas [@chesapeake:2025; @edgetech:2025]. After cropping, the images must then be manually re-analyzed and labeled in another software such as `LabelMe`, adding further to the labor-intensive workflow.

To the best of our knowledge, there is currently no open-source software available for viewing, manipulating, and annotating side-scan sonar files. Even commercial software does not provide a streamlined workflow optimized for time efficiency. Our open-source and free-to-use software, `SideScanSonarEditor`, significantly simplifies and accelerates the annotation process for sonar data. The output format is designed for easy analysis, further processing, and seamless integration with object detection or segmentation models [@lin:2014].

`SideScanSonarEditor` utilizes the pyxtf library to read complete XTF files and generates waterfall views of surveyed areas [@oysstupyxtf:2025]. The data is displayed as a collection of pings, with the scan direction oriented from bottom to top. The image view consists of two sections corresponding to the two sides of the tow-fish: the port side and the starboard side, with port-side data being horizontally flipped for accurate real-world representation of the seafloor. The software’s primary function is to generate waterfall images and enable efficient annotation of targets, as well as cropping tiles to create datasets ready for model training.

# Future Work

The side-scan sonar data can be saved in numerous different formats (XTF, JSF, GCF and more). In future software updates support for more formats will be added. Furthermore the data formats can hold additional information like bathymetry data which can also be analysed or used for machine learning purposes, thus support for these data types will be added in the future.
Additional sonar data correction and image manipulation functions will also be added in the future including bottom tracking or color palette change.
In current form the tool is very simple but future versions might include an improved drawing methods and more predefined shapes. More output formats may also be added in the future including PASCAL VOC and YOLO.

# Acknowledgements

This work was supported by the Port City Innovation Hub (European Regional Development Fund).

# References
