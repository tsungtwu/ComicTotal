<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Thanks again! Now go create something AMAZING! :D
***
***
***
*** To avoid retyping too much info. Do a search and replace for the following:
*** tsungtwu, ComicTotal, twitter_handle, email, ComicTotal, project_description
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

<!-- [![Stargazers][stars-shield]][stars-url] -->
<!-- [![Issues][issues-shield]][issues-url] -->
<!-- [![MIT License][license-shield]][license-url] -->




<!-- PROJECT LOGO -->
<br />
<p align="center">
  <!-- <a href="https://github.com/tsungtwu/ComicTotal">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a> -->

  <h3 align="center">ComicTotal</h3>

  <p align="center">
    Subscribe and manage Comic from multiple source
    <br />
    <!-- <a href="https://github.com/tsungtwu/ComicTotal"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/tsungtwu/ComicTotal">View Demo</a> -->
    ·
    <a href="https://github.com/tsungtwu/ComicTotal/issues">Report Bug</a>
    ·
    <a href="https://github.com/tsungtwu/ComicTotal/issues">Request Feature</a>
  </p>
</p>



<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary><h2 style="display: inline-block">Table of Contents</h2></summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgements">Acknowledgements</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

<!-- [![Product Name Screen Shot][product-screenshot]](https://example.com) -->
Subscribe and manage Comic from multiple source



### Built With

* [Airflow](https://airflow.apache.org/)
* [ComicCrawler](https://github.com/eight04/ComicCrawler)




<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple steps.

### Prerequisites

* pip
* docker
* docker-compose


### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/tsungtwu/ComicTotal.git
   ```
2. Build docker image
   ```sh
    docker build -t comictotal:2.1.2 .
   ```
3. Running Airflow in Docker

    ref: https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html
   ```sh
    mkdir -p ./dags ./logs ./plugins
    echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_GID=0" > .env
    docker-compose up airflow init
    docker-compose up
   ```


<!-- USAGE EXAMPLES -->
## Usage

1. run init_comic dag with config
    ```
    {"url": "COMIC_URL"}
    ```


<!-- _For more examples, please refer to the [Documentation](https://example.com)_ -->



<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/tsungtwu/ComicTotal/issues) for a list of proposed features (and known issues).



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.



<!-- CONTACT -->
## Contact


Project Link: [https://github.com/tsungtwu/ComicTotal](https://github.com/tsungtwu/ComicTotal)



<!-- ACKNOWLEDGEMENTS -->
<!-- ## Acknowledgements

* []()
* []()
* []() -->





<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/tsungtwu/repo.svg?style=for-the-badge
[contributors-url]: https://github.com/tsungtwu/ComicTotal/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/tsungtwu/repo.svg?style=for-the-badge
[forks-url]: https://github.com/tsungtwu/ComicTotal/network/members
[stars-shield]: https://img.shields.io/github/stars/tsungtwu/repo.svg?style=for-the-badge
[stars-url]: https://github.com/tsungtwu/ComicTotal/stargazers
[issues-shield]: https://img.shields.io/github/issues/tsungtwu/repo.svg?style=for-the-badge
[issues-url]: https://github.com/tsungtwu/ComicTotal/issues
[license-shield]: https://img.shields.io/github/license/tsungtwu/repo.svg?style=for-the-badge
[license-url]: https://github.com/tsungtwu/ComicTotal/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/tsungtwu