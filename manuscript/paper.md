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
    corresponding: true
    affiliation: 1
affiliations:
 - name: Science of Intelligence, University of Liverpool, United Kingdom
   index: 1

date: 25 February 2025
bibliography: bibliography.bib
---

# Summary

Side-scan sonars are commonly used devices for mapping of the seafloor.
The collected data allows for generation of a detailed imagery of the surveyed area [1].
The typical use cases of side-scan sonar include:
 - Marine aarcheology
 - Underwater topography
 - Underwater security
 - Resource exploration
Annotation of the targets is typically done using specialised software which does not produce results allowing quick conversion to formats commonly used to train machine learning models.
`SideScanSonarEditor` is a free and open-source Python package which allows the user to load sonar data from XTF file as images and annotate them [2].
The tool allows for drawing of polygon shape around objects of interest as well as rectangular shapes as tiles for cropping of the areas as smaller images.
(\autoref{fig:overview}).

`SideScanSonarEditor` provides the following sonar imagee manipulation methods:

 - Decimation – across track down sampling which might be useful when importing very large files that might exceed memory limits on some systems.
   The decimation factor directly determines the fraction of the data that is to be retained meaning with a factor of 1 a 100% of the samples are loaded, with a factor of 2, 50%, factor of 3, 33% and so on. The setting range goes from 1-10 but in reality, values greater than 4 will produce errors or severely reduce number of samples leading to loss of significant portion of data. For the purpose of this research decimation is set to 1 at all times to ensure the highest number of horizontal features per target.
 - Stretch – Along track stretch factor which defines how many times each ping should be repeated. This method is applied to improve the visual representation of the features. Typically, when the data is displayed, the objects will appear stretched horizontally and compressed vertically. To compensate without losing across track features the image is expanded vertically allowing for easier analysis and labelling of the targets. The stretching method, however, is not utilised when generating training data or during inference. The technique is used purely as a visual correction during the annotation process. 
 - Invert – Inversion of the colour palette which in some cases might help in visual recognition of targets.
 - Colour mapping – Setting colour palette to highlight different features. Applying different mapping scales can help distinguish various targets on the image. Currently available options include two greyscale patterns a linear (grey) and logarithmic (greylog).
 - Map range – Minimum and maximum mapping ranges are by default automatically calculated based on the intensity input data. Both can be manually modified to change representation of the features for easier interpretation.
 - Slant range correction - apply slant rage correction to compensate for the geometric distortion of the return signal. The corrected image represents true seafloor distances allowing for better alignment with the navigation data [1], [3].

![SideScanSonarEditor app \label{fig:overview}](overview.png)

# Statement of Need

The interpretation of the sonar data is typically conducted using propriatary software specifically designed to analyse such data and provide extensive post-processing capabilities. These software packages however do not allow for extraction of the imagery and annotations in a format allowing easy training of computer vision models. For the purpose of training automatic target recognition model the imagery had to be manually cropped in SonarWiz to then be annotated using LabelMe or other standard annotating tool. This process took a very long time because it required visual analysis of the sonar swaths in SonarWiz or EdgeTech Discover and assigning areas meant for cropping [4], [5]. After the cropping process was completed, the images had to be analysed again this time in LabelMe specifically with the purpose of labelling. To simplify and speed up the process as well as allowing for custom manipulation of the data a SideScanSonarEditor was developed. SideScanSonarEditor using pyxtf library reads entire XTF file and generates a waterfall view of the surveyed area [6]. The data is displayed as a collection of pings with the direction of the scan being from bottom to the top. The image view consists of two parts: port side and starboard side, with port side data being horizontally flipped for real world representation of the seafloor. The primary function is to generate waterfall images and allow for annotation of the targets as well as cropping tiles with them creating a dataset ready for model training. The software allows for creation, edition and removal of class labels and drawing polygons around objects of interest. The unlimited zoom allows for very close inspection of the area and precise labelling which is crucial considering that the research is focused on the detection of very small objects like boulders. Furthermore, a tile cropping ability was added allowing selection of exact areas for extraction in a form of rectangular tiles. Initial attempts in automatic cropping resulted in duplicates or incomplete object cropping potentially having negative impact on the trained model, thus it was decided that manual drawing of crop tiles will provide the best results. Each channel (port side, starboard side) can be separately modified by using a set of simple tools to change the appearance of the visualisation. The user can choose to invert the colour mapping and normalise intensity of the pixels to highlight different features. The resulting annotations are saved in a commonly used COCO format which allows direct training without any additional processing or conversion [7]. For easier testing of the trained model the navigation data is also stored in the COCO format as extra keys allowing for shape estimation and viualisation of targets using their georeferenced positions.

# Future Work

The side-scan sonar data can be saved in numerous different formats (XTF, JSF, GCF and more). In the future support for more formats may be added.
Additional sonar data correction and image manipulation functions may be added in the future including bottom tracking or colour palette change.
In current form the tool is very simple but future version might see an improved drawing methods and more predefined shapes.
More output formats may be added in the future including PASCAL VOC and YOLO.

# Acknowledgements

This work was supported by the Port City Innovation Hub (European Regional Development Fund).

# References

\pagebreak
\appendix


